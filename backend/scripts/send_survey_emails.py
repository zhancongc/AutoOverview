#!/usr/bin/env python3
"""
发送用户调研邮件 — 流失用户反馈调研 + 加微信送积分

目标：找到用过产品但没有持续使用的真实用户，真诚请教原因，以 4 积分作为感谢。

用法:
    cd backend && python3 scripts/send_survey_emails.py                        # 预览待发送用户（不实际发送）
    cd backend && python3 scripts/send_survey_emails.py --send                 # 实际发送
    cd backend && python3 scripts/send_survey_emails.py --send --limit 5       # 只发 5 封
    cd backend && python3 scripts/send_survey_emails.py --send --delay 8       # 每封间隔 8 秒
    cd backend && python3 scripts/send_survey_emails.py --email xxx@sjtu.edu.cn  # 只给指定邮箱预览/发送
    cd backend && python3 scripts/send_survey_emails.py --send --resend        # 重新发送已发过的
    cd backend && python3 scripts/send_survey_emails.py --min-days 14          # 最后使用至少 14 天前
    cd backend && python3 scripts/send_survey_emails.py --max-days 60          # 最后使用不超过 60 天
"""
import argparse
import os
import smtplib
import sys
import time
from datetime import datetime, timedelta, timezone

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.auth"), override=True)

from sqlalchemy import text

from database import db
from authkit.core.config import config
from authkit.templates.survey_email import render_survey_email
from authkit.routers.email_unsubscribe import generate_unsubscribe_url

# ── 配置 ──────────────────────────────────────────────

# 开发者自己的账号，永远排除
EXCLUDE_EMAILS = {
    "zhancongc@icloud.com",
    "zhancongc@gmail.com",
    "alipay_050yHjs_ZeJUgiLf@oauth.danmo.tech",
}

WECHAT_ID = "zhancongc"

# 微信二维码 URL（前端 public 目录下的文件）
SITE_URL = os.getenv("SITE_URL", "https://scholar.danmo.tech")
QRCODE_URL = f"{SITE_URL}/wechat-qr.jpg"


# ── 邮件发送 ──────────────────────────────────────────

def send_email(to_email: str, subject: str, html_content: str, text_content: str) -> tuple[bool, str]:
    """发送单封邮件。返回 (成功?, 错误信息)。"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{config.SMTP_FROM_NAME} <{config.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Reply-To"] = config.SMTP_USER  # 用户直接回复到发件邮箱
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


# ── 建表（仅在脚本运行时） ────────────────────────────

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS survey_emails (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    email VARCHAR(255) NOT NULL,
    nickname VARCHAR(100),
    topic VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(email)
);
"""


def ensure_table(session):
    """确保 survey_emails 表存在。"""
    session.execute(text(CREATE_TABLE_SQL))
    session.commit()


# ── 查询目标用户 ──────────────────────────────────────

def find_target_users(session, args) -> list[dict]:
    """查询流失用户：生成过综述的 + 注册后从未使用的。"""
    params = {}

    # 基础排除条件
    exclude_list = list(EXCLUDE_EMAILS)
    if args.exclude:
        for e in args.exclude.split(","):
            e = e.strip().lower()
            if e:
                exclude_list.append(e)
    placeholders = ", ".join(f":ex{i}" for i in range(len(exclude_list)))
    for i, e in enumerate(exclude_list):
        params[f"ex{i}"] = e

    # 指定邮箱
    email_filter = ""
    if args.email:
        email_filter = " AND u.email = :target_email"
        params["target_email"] = args.email.strip().lower()

    # 已发排除（除非 --resend）
    sent_filter = ""
    if not args.resend:
        sent_filter = " AND NOT EXISTS (SELECT 1 FROM survey_emails se WHERE se.email = u.email)"

    # 时间过滤
    min_days = args.min_days
    max_days = args.max_days
    task_time = ""
    reg_time = ""
    if min_days:
        params["min_date"] = datetime.now(timezone.utc) - timedelta(days=min_days)
        task_time += " AND lt.created_at < :min_date"
        reg_time += " AND u.created_at < :min_date"
    if max_days:
        params["max_date"] = datetime.now(timezone.utc) - timedelta(days=max_days)
        task_time += " AND lt.created_at > :max_date"
        reg_time += " AND u.created_at > :max_date"

    query = text(f"""
        -- 1) 生成过综述的用户（带主题）
        SELECT u.id, u.email, u.nickname,
               lt.topic,
               lt.created_at AS last_task_at,
               false AS never_used
        FROM users u
        JOIN (
            SELECT user_id, topic, created_at,
                   ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
            FROM review_tasks
            WHERE user_id IS NOT NULL
        ) lt ON lt.user_id = u.id AND lt.rn = 1
        WHERE u.email NOT IN ({placeholders})
          {email_filter}
          {task_time}
          {sent_filter}

        UNION ALL

        -- 2) 注册后从未生成综述的用户
        SELECT u.id, u.email, u.nickname,
               NULL AS topic,
               u.created_at AS last_task_at,
               true AS never_used
        FROM users u
        WHERE NOT EXISTS (SELECT 1 FROM review_tasks rt WHERE rt.user_id = u.id)
          AND u.email NOT IN ({placeholders})
          {email_filter}
          {reg_time}
          {sent_filter}

        ORDER BY last_task_at DESC
    """)

    rows = session.execute(query, params).fetchall()
    users = []
    for r in rows:
        topic = r[3] or ""
        # 只取第一行作为标题，去掉摘要/关键词等后续内容
        topic = topic.split("\n")[0].strip()[:80]
        users.append(dict(
            user_id=r[0], email=r[1], nickname=r[2], topic=topic,
            last_task_at=r[4], never_used=r[5],
        ))
    return users


# ── 主流程 ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="发送用户调研邮件（流失用户反馈 + 加微信送积分）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  预览待发送用户:
    python3 scripts/send_survey_emails.py

  实际发送:
    python3 scripts/send_survey_emails.py --send

  只发给指定用户:
    python3 scripts/send_survey_emails.py --send --email someone@sjtu.edu.cn

  发给 14~60 天未使用的用户，每封间隔 8 秒:
    python3 scripts/send_survey_emails.py --send --min-days 14 --max-days 60 --delay 8
        """,
    )
    parser.add_argument("--send", action="store_true", help="实际发送（默认仅预览）")
    parser.add_argument("--email", help="只发送给指定邮箱")
    parser.add_argument("--limit", type=int, default=0, help="最大发送数量（0=不限）")
    parser.add_argument("--delay", type=float, default=8.0, help="每封邮件间隔秒数（默认 8）")
    parser.add_argument("--min-days", type=int, default=7, help="最后使用至少 N 天前（默认 7）")
    parser.add_argument("--max-days", type=int, default=90, help="最后使用不超过 N 天前（默认 90）")
    parser.add_argument("--resend", action="store_true", help="重新发送已发过的邮件")
    parser.add_argument("--exclude", help="额外排除的邮箱（逗号分隔）")
    args = parser.parse_args()

    for session in db.get_session():
        ensure_table(session)

        users = find_target_users(session, args)
        if not users:
            print("没有符合条件的用户")
            return

        if args.limit:
            users = users[: args.limit]

        # 预览模式
        if not args.send:
            used = [u for u in users if not u["never_used"]]
            unused = [u for u in users if u["never_used"]]
            print(f"找到 {len(users)} 个待调研用户（预览模式，加 --send 实际发送）")
            print(f"  生成过综述: {len(used)} 人")
            print(f"  注册未使用: {len(unused)} 人\n")
            for i, u in enumerate(users, 1):
                tag = "[未使用]" if u["never_used"] else ""
                days_ago = ""
                if u["last_task_at"]:
                    delta = datetime.now(timezone.utc) - u["last_task_at"].replace(tzinfo=timezone.utc) if u["last_task_at"].tzinfo is None else datetime.now(timezone.utc) - u["last_task_at"]
                    days_ago = f"  ({delta.days} 天前)"
                print(f"  {i}. {tag}{u['nickname'] or '未设置昵称'} <{u['email']}>{days_ago}")
                if u["topic"]:
                    print(f"     主题: 《{u['topic'][:60]}{'…' if len(u['topic']) > 60 else ''}》")
                print()

            # 渲染两种样本
            for label, sample_list in [("生成过综述", used), ("注册未使用", unused)]:
                if not sample_list:
                    continue
                sample = sample_list[0]
                unsubscribe_url = generate_unsubscribe_url(sample["email"])
                subject, html, txt = render_survey_email(
                    topic=sample["topic"] or "",
                    never_used=sample["never_used"],
                    wechat_id=WECHAT_ID,
                    qrcode_url=QRCODE_URL,
                    unsubscribe_url=unsubscribe_url,
                )
                print(f"── {label} 邮件样本（{sample['email']}）──")
                print(f"Subject: {subject}\n")
                print(txt)
                print()
            return

        # 实际发送
        print(f"准备发送 {len(users)} 封调研邮件（间隔 {args.delay}s）\n")

        sent_count = 0
        failed_count = 0

        for i, u in enumerate(users, 1):
            nickname = u["nickname"] or "同学"
            topic = u["topic"] or ""
            email = u["email"]

            unsubscribe_url = generate_unsubscribe_url(email)
            subject, html, txt = render_survey_email(
                topic=topic,
                never_used=u["never_used"],
                wechat_id=WECHAT_ID,
                qrcode_url=QRCODE_URL,
                unsubscribe_url=unsubscribe_url,
            )

            ok, err = send_email(email, subject, html, txt)

            if ok:
                # 更新 survey_emails 表
                session.execute(text("""
                    INSERT INTO survey_emails (user_id, email, nickname, topic, status, sent_at)
                    VALUES (:uid, :email, :nickname, :topic, 'sent', NOW())
                    ON CONFLICT (email) DO UPDATE SET status='sent', sent_at=NOW(), error=NULL
                """), dict(uid=u["user_id"], email=email, nickname=nickname, topic=topic[:500]))
                # 同步写入 email_contacts 以支持退订
                session.execute(text("""
                    INSERT INTO email_contacts (email, name, status, unsubscribed)
                    VALUES (:email, :name, 'sent', false)
                    ON CONFLICT (email) DO NOTHING
                """), dict(email=email, name=nickname))
                session.commit()
                sent_count += 1
                topic_preview = f"《{topic[:30]}…》" if len(topic) > 30 else f"《{topic}》" if topic else "(无主题)"
                print(f"[{i}/{len(users)}] ✓ {nickname} <{email}> {topic_preview}")
            else:
                session.execute(text("""
                    INSERT INTO survey_emails (user_id, email, nickname, topic, status, error)
                    VALUES (:uid, :email, :nickname, :topic, 'failed', :error)
                    ON CONFLICT (email) DO UPDATE SET status='failed', error=:error
                """), dict(uid=u["user_id"], email=email, nickname=nickname, topic=topic[:500], error=err[:500]))
                session.commit()
                failed_count += 1
                print(f"[{i}/{len(users)}] ✗ {nickname} <{email}> — {err}")

            if args.delay > 0 and i < len(users):
                time.sleep(args.delay)

        # 统计
        print(f"\n发送完成:")
        print(f"  成功: {sent_count}")
        print(f"  失败: {failed_count}")
        print(f"  总计: {sent_count + failed_count}")

        if failed_count == 0:
            print(f"\n全部发送成功！记得关注邮箱回复和微信好友申请。")
            print(f"收到反馈后，用以下命令发放积分:")
            print(f"  cd backend && python3 scripts/adjust_credits.py --email <邮箱> --amount 4 --reason 'survey_feedback'")


if __name__ == "__main__":
    main()
