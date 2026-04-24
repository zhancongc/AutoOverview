#!/usr/bin/env python3
"""
批量发送推广邮件

用法:
    cd backend && python3 scripts/send_promo_emails.py                        # 发送所有 pending
    cd backend && python3 scripts/send_promo_emails.py --limit 10             # 只发 10 封
    cd backend && python3 scripts/send_promo_emails.py --position "PhD"       # 只发 PhD
    cd backend && python3 scripts/send_promo_emails.py --email someone@ac.uk  # 发给指定邮箱
    cd backend && python3 scripts/send_promo_emails.py --limit 50 --delay 5   # 每封间隔 5 秒
    cd backend && python3 scripts/send_promo_emails.py --dry-run              # 只预览不发送
"""
import argparse
import sys
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()  # 先加载 .env（数据库等配置）
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.auth"), override=True)  # .env.auth 覆盖 SMTP 配置

from sqlalchemy import text

from database import db
from authkit.core.config import config
from authkit.templates.promo_email import render_promo_email
from authkit.routers.email_unsubscribe import generate_unsubscribe_url
from scripts.university_domains import get_university, get_university_abbrev


def send_email(to_email: str, subject: str, html_content: str, text_content: str) -> tuple[bool, str]:
    """发送单封邮件。返回 (成功?, 错误信息)。"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{config.SMTP_FROM_NAME} <{config.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        if config.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as server:
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
                server.starttls()
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
                server.send_message(msg)

        return True, ""
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="批量发送推广邮件")
    parser.add_argument("--email", help="只发送给指定邮箱")
    parser.add_argument("--position", help="只发送给指定职位（模糊匹配）")
    parser.add_argument("--limit", type=int, default=0, help="最大发送数量（0=不限）")
    parser.add_argument("--delay", type=float, default=5.0, help="每封邮件间隔秒数（默认 5）")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不实际发送")
    parser.add_argument("--reset", help="重置指定邮箱的状态为 pending（可指定多个，逗号分隔）")
    args = parser.parse_args()

    for session in db.get_session():
        # 重置状态
        if args.reset:
            emails = [e.strip() for e in args.reset.split(",") if e.strip()]
            for email in emails:
                session.execute(text("""
                    UPDATE email_contacts SET status='pending', sent_at=NULL, error=NULL
                    WHERE email=:email
                """), dict(email=email))
            session.commit()
            print(f"已重置 {len(emails)} 个邮箱状态为 pending")

        # 构建查询
        query = "SELECT id, name, email, position FROM email_contacts WHERE status='pending' AND (unsubscribed IS NULL OR unsubscribed = false)"
        params = {}

        if args.email:
            query += " AND email=:email"
            params["email"] = args.email.strip().lower()
        if args.position:
            query += " AND position ILIKE :position"
            params["position"] = f"%{args.position}%"

        query += " ORDER BY id"

        if args.limit:
            query += f" LIMIT {args.limit}"

        rows = session.execute(text(query), params).fetchall()

        if not rows:
            print("没有符合条件的待发送联系人")
            return

        print(f"找到 {len(rows)} 个待发送联系人")
        if args.dry_run:
            print("--- DRY RUN 模式 ---")
        print()

        sent = 0
        failed = 0

        for i, (cid, name, email, position) in enumerate(rows, 1):
            # 推断大学
            university = get_university(email)

            # 渲染邮件
            unsubscribe_url = generate_unsubscribe_url(email)
            subject, html, txt = render_promo_email(
                name=name or "Researcher",
                university=university,
                unsubscribe_url=unsubscribe_url,
            )

            if args.dry_run:
                print(f"[{i}/{len(rows)}] {name} <{email}>")
                print(f"  大学: {university or '未知'}")
                print(f"  Subject: {subject}")
                print()
                sent += 1
                continue

            # 实际发送
            ok, err = send_email(email, subject, html, txt)

            if ok:
                session.execute(text("""
                    UPDATE email_contacts SET status='sent', sent_at=NOW(), error=NULL
                    WHERE id=:id
                """), dict(id=cid))
                session.commit()
                sent += 1
                print(f"[{i}/{len(rows)}] ✓ {name} <{email}>")
            else:
                session.execute(text("""
                    UPDATE email_contacts SET status='failed', error=:error
                    WHERE id=:id
                """), dict(id=cid, error=err[:500]))
                session.commit()
                failed += 1
                print(f"[{i}/{len(rows)}] ✗ {name} <{email}> — {err}")

            # 延迟
            if args.delay > 0 and i < len(rows) and not args.dry_run:
                time.sleep(args.delay)

        # 统计
        print(f"\n发送完成:")
        print(f"  成功: {sent}")
        print(f"  失败: {failed}")
        print(f"  总计: {sent + failed}")

        # 剩余 pending
        remaining = session.execute(text("SELECT COUNT(*) FROM email_contacts WHERE status='pending' AND (unsubscribed IS NULL OR unsubscribed = false)")).scalar()
        if remaining:
            print(f"  剩余未发送: {remaining}")

        # 已退订
        unsubscribed = session.execute(text("SELECT COUNT(*) FROM email_contacts WHERE unsubscribed = true")).scalar()
        if unsubscribed:
            print(f"  已退订: {unsubscribed}")


if __name__ == "__main__":
    main()
