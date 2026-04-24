#!/usr/bin/env python3
"""
调整用户积分

用法:
    cd backend && python3 scripts/adjust_credits.py --email user@example.com --change +10 --reason "补偿" --detail "客服手动补偿"
    cd backend && python3 scripts/adjust_credits.py --user-id 123 --change -5 --reason "扣减" --detail "误充退回"
    cd backend && python3 scripts/adjust_credits.py --email user@example.com --set 20 --reason "修正" --detail "对账修正为20"
    cd backend && python3 scripts/adjust_credits.py --email user@example.com --query  # 查询余额和变动记录
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text, desc
from database import db


def get_user(session, email=None, user_id=None):
    """查找用户"""
    if user_id:
        row = session.execute(text("SELECT id, email, meta_data FROM users WHERE id = :id"), {"id": user_id}).fetchone()
    elif email:
        row = session.execute(text("SELECT id, email, meta_data FROM users WHERE email = :email"), {"email": email}).fetchone()
    else:
        print("请指定 --email 或 --user-id")
        sys.exit(1)

    if not row:
        print(f"用户不存在: {email or user_id}")
        sys.exit(1)

    return row


def get_credits(meta_data_str):
    import json
    if meta_data_str:
        try:
            return json.loads(meta_data_str).get("review_credits", 0)
        except Exception:
            return 0
    return 0


def set_credits(session, user_id, meta_data_str, new_credits):
    import json
    meta = json.loads(meta_data_str) if meta_data_str else {}
    old_credits = meta.get("review_credits", 0)
    meta["review_credits"] = new_credits
    session.execute(text("UPDATE users SET meta_data = :meta WHERE id = :id"),
                    {"meta": json.dumps(meta), "id": user_id})
    return old_credits


def log_change(session, user_id, change, balance_before, balance_after, reason, detail, operator):
    """记录积分变动"""
    session.execute(text("""
        INSERT INTO credit_logs (user_id, change, balance_before, balance_after, reason, detail, operator)
        VALUES (:user_id, :change, :before, :after, :reason, :detail, :operator)
    """), dict(user_id=user_id, change=change, before=balance_before,
              after=balance_after, reason=reason, detail=detail or "", operator=operator))


def main():
    parser = argparse.ArgumentParser(description="调整用户积分")
    parser.add_argument("--email", help="用户邮箱")
    parser.add_argument("--user-id", type=int, help="用户 ID")
    parser.add_argument("--change", type=int, help="积分变动量（如 +10 或 -5）")
    parser.add_argument("--set", type=int, dest="set_value", help="直接设置积分为指定值")
    parser.add_argument("--reason", required=False, default="adjust", help="变动原因（register/payment/consume/refund/adjust）")
    parser.add_argument("--detail", default="", help="详细说明")
    parser.add_argument("--operator", default="admin", help="操作者标识")
    parser.add_argument("--query", action="store_true", help="查询积分余额和最近变动")
    args = parser.parse_args()

    if not args.email and not args.user_id:
        print("请指定 --email 或 --user-id")
        sys.exit(1)

    for session in db.get_session():
        user = get_user(session, email=args.email, user_id=args.user_id)
        user_id, email, meta_data = user[0], user[1], user[2]
        current_credits = get_credits(meta_data)

        # 查询模式
        if args.query:
            print(f"用户: {email} (ID: {user_id})")
            print(f"当前积分: {current_credits}")
            print()
            rows = session.execute(text("""
                SELECT change, balance_before, balance_after, reason, detail, operator, created_at
                FROM credit_logs WHERE user_id = :uid
                ORDER BY created_at DESC LIMIT 20
            """), {"uid": user_id}).fetchall()

            if rows:
                print(f"{'时间':<20} {'变动':>6} {'变动前':>6} {'变动后':>6} {'原因':<12} {'说明':<20} {'操作者':<8}")
                print("-" * 90)
                for change, before, after, reason, detail, op, ts in rows:
                    ts_str = ts.strftime("%Y-%m-%d %H:%M") if ts else ""
                    sign = "+" if change > 0 else ""
                    print(f"{ts_str:<20} {sign}{change:>5} {before:>6} {after:>6} {reason:<12} {(detail or ''):<20} {op:<8}")
            else:
                print("暂无变动记录")
            return

        # 变动模式
        if args.set_value is not None:
            new_credits = args.set_value
            change = new_credits - current_credits
        elif args.change is not None:
            change = args.change
            new_credits = current_credits + change
        else:
            print("请指定 --change 或 --set")
            sys.exit(1)

        if new_credits < 0:
            print(f"积分不能为负数（当前 {current_credits}，变动 {change:+d}，结果 {new_credits}）")
            sys.exit(1)

        # 更新积分
        old_credits = set_credits(session, user_id, meta_data, new_credits)

        # 记录日志
        log_change(session, user_id, change, old_credits, new_credits,
                    args.reason, args.detail, args.operator)
        session.commit()

        print(f"用户: {email}")
        print(f"积分变动: {old_credits} → {new_credits} ({change:+d})")
        print(f"原因: {args.reason}")
        if args.detail:
            print(f"说明: {args.detail}")


if __name__ == "__main__":
    main()
