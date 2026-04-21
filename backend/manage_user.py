#!/usr/bin/env python3
"""
用户管理工具脚本

功能：
1. 设置综述状态（免费生成待解锁 / 付费生成已解锁）
2. 增加/减少免费额度 (free_credits)
3. 增加/减少付费额度 (review_credits)
4. 增加/减少搜索次数 (search_bonus) / 清除今日搜索记录

使用示例：
    # 设置综述为免费生成待解锁状态
    python manage_user.py set-record-status --email user@example.com --topic "xxx" -- unpaid

    # 设置综述为付费生成已解锁状态
    python manage_user.py set-record-status --email user@example.com --topic "xxx" -- paid

    # 增加免费额度
    python manage_user.py update-credits --email user@example.com --free-credits +1

    # 减少免费额度
    python manage_user.py update-credits --email user@example.com --free-credits -1

    # 增加付费额度
    python manage_user.py update-credits --email user@example.com --paid-credits +3

    # 设置付费额度
    python manage_user.py update-credits --email user@example.com --paid-credits 5

    # 增加 5 次额外搜索次数
    python manage_user.py update-search --email user@example.com --bonus +5

    # 清除今日搜索记录（重置为 0/5）
    python manage_user.py update-search --email user@example.com --reset

    # 查看用户信息
    python manage_user.py show-user --email user@example.com
"""
import argparse
import sys
import os
import psycopg2
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env')

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'paper'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'security')
}


def get_connection():
    """获取数据库连接"""
    return psycopg2.connect(**DB_CONFIG)


def get_user_by_email(cursor, email):
    """根据邮箱获取用户"""
    cursor.execute("SELECT id, email FROM users WHERE email = %s", (email,))
    return cursor.fetchone()


def show_user(email):
    """显示用户信息"""
    conn = get_connection()
    cur = conn.cursor()

    try:
        user = get_user_by_email(cur, email)
        if not user:
            print(f"❌ 用户不存在: {email}")
            return False

        user_id, user_email = user
        print(f"\n{'='*60}")
        print(f"用户信息")
        print(f"{'='*60}")
        print(f"ID: {user_id}")
        print(f"邮箱: {user_email}")

        # 获取用户元数据
        cur.execute("SELECT meta_data FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if row and row[0]:
            import json
            meta_data = json.loads(row[0])
            print(f"\n额度信息:")
            print(f"  免费额度 (free_credits): {meta_data.get('free_credits', 0)}")
            print(f"  付费额度 (review_credits): {meta_data.get('review_credits', 0)}")
            print(f"  已购买 (has_purchased): {meta_data.get('has_purchased', False)}")

            # 搜索次数信息
            import time
            timestamps = meta_data.get('search_timestamps', [])
            cutoff = time.time() - 86400
            recent_count = len([ts for ts in timestamps if ts > cutoff])
            print(f"\n搜索次数:")
            print(f"  今日已用: {recent_count}")
            print(f"  每日上限: {os.getenv('DAILY_SEARCH_LIMIT', '5')}")
            print(f"  额外搜索次数 (search_bonus): {meta_data.get('search_bonus', 0)}")

        # 获取综述记录
        cur.execute("""
            SELECT id, topic, is_paid, created_at
            FROM review_records
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        records = cur.fetchall()

        print(f"\n综述记录 ({len(records)} 条):")
        for r in records:
            record_id, topic, is_paid, created_at = r
            status = "✅ 已付费" if is_paid else "🔒 待付费"
            print(f"  [{record_id}] {topic}")
            print(f"      状态: {status} | 创建时间: {created_at}")

        print(f"{'='*60}\n")
        return True

    finally:
        cur.close()
        conn.close()


def set_record_status(email, topic=None, record_id=None, paid=False):
    """设置综述状态"""
    conn = get_connection()
    cur = conn.cursor()

    try:
        user = get_user_by_email(cur, email)
        if not user:
            print(f"❌ 用户不存在: {email}")
            return False

        user_id, _ = user

        # 构建查询条件
        if record_id:
            cur.execute("""
                SELECT id, topic, is_paid
                FROM review_records
                WHERE user_id = %s AND id = %s
            """, (user_id, record_id))
        elif topic:
            cur.execute("""
                SELECT id, topic, is_paid
                FROM review_records
                WHERE user_id = %s AND topic = %s
            """, (user_id, topic))
        else:
            print("❌ 请指定 --topic 或 --record-id")
            return False

        record = cur.fetchone()
        if not record:
            print(f"❌ 综述记录不存在")
            return False

        record_id, record_topic, current_status = record

        # 更新状态
        new_status = '已付费 (无水印)' if paid else '待付费 (有水印)'
        cur.execute("""
            UPDATE review_records
            SET is_paid = %s
            WHERE id = %s
        """, (paid, record_id))

        conn.commit()

        print(f"✅ 综述状态已更新")
        print(f"  ID: {record_id}")
        print(f"  主题: {record_topic}")
        print(f"  原状态: {'已付费' if current_status else '待付费'}")
        print(f"  新状态: {new_status}")
        return True

    finally:
        cur.close()
        conn.close()


def update_credits(email, free_credits=None, paid_credits=None):
    """更新用户额度"""
    conn = get_connection()
    cur = conn.cursor()

    try:
        user = get_user_by_email(cur, email)
        if not user:
            print(f"❌ 用户不存在: {email}")
            return False

        user_id, _ = user

        # 获取当前元数据
        cur.execute("SELECT meta_data FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            meta_data = {}
        else:
            import json
            meta_data = json.loads(row[0])

        current_free = meta_data.get('free_credits', 0)
        current_paid = meta_data.get('review_credits', 0)

        # 处理额度变更
        new_free = current_free
        new_paid = current_paid

        if free_credits is not None:
            if isinstance(free_credits, str) and free_credits.startswith(('+', '-')):
                # 相对增减
                delta = int(free_credits)
                new_free = current_free + delta
                print(f"免费额度: {current_free} {free_credits} = {new_free}")
            else:
                # 绝对值设置
                new_free = int(free_credits)
                print(f"免费额度: {current_free} -> {new_free}")

        if paid_credits is not None:
            if isinstance(paid_credits, str) and paid_credits.startswith(('+', '-')):
                delta = int(paid_credits)
                new_paid = current_paid + delta
                print(f"付费额度: {current_paid} {paid_credits} = {new_paid}")
            else:
                new_paid = int(paid_credits)
                print(f"付费额度: {current_paid} -> {new_paid}")

        # 更新元数据
        meta_data['free_credits'] = new_free
        meta_data['review_credits'] = new_paid

        # 更新数据库
        cur.execute("""
            UPDATE users
            SET meta_data = %s
            WHERE id = %s
        """, (json.dumps(meta_data), user_id))

        conn.commit()

        print(f"\n✅ 额度更新成功")
        print(f"  用户: {email}")
        print(f"  免费额度: {new_free}")
        print(f"  付费额度: {new_paid}")
        return True

    finally:
        cur.close()
        conn.close()


def update_search(email, bonus=None, reset=False):
    """更新用户搜索次数"""
    import time
    import json

    conn = get_connection()
    cur = conn.cursor()

    try:
        user = get_user_by_email(cur, email)
        if not user:
            print(f"❌ 用户不存在: {email}")
            return False

        user_id, _ = user

        # 获取当前元数据
        cur.execute("SELECT meta_data FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            meta_data = {}
        else:
            meta_data = json.loads(row[0])

        current_bonus = meta_data.get('search_bonus', 0)
        timestamps = meta_data.get('search_timestamps', [])
        cutoff = time.time() - 86400
        recent_count = len([ts for ts in timestamps if ts > cutoff])

        if reset:
            # 清除 24h 内的搜索时间戳
            meta_data['search_timestamps'] = [ts for ts in timestamps if ts <= cutoff]
            print(f"今日搜索记录已清除: {recent_count} -> 0")

        if bonus is not None:
            if isinstance(bonus, str) and bonus.startswith(('+', '-')):
                delta = int(bonus)
                new_bonus = current_bonus + delta
                print(f"额外搜索次数: {current_bonus} {bonus} = {new_bonus}")
            else:
                new_bonus = int(bonus)
                print(f"额外搜索次数: {current_bonus} -> {new_bonus}")
            meta_data['search_bonus'] = new_bonus

        # 更新数据库
        cur.execute("""
            UPDATE users
            SET meta_data = %s
            WHERE id = %s
        """, (json.dumps(meta_data), user_id))

        conn.commit()

        # 显示更新后的状态
        updated_timestamps = meta_data.get('search_timestamps', [])
        updated_recent = len([ts for ts in updated_timestamps if ts > time.time() - 86400])
        print(f"\n✅ 搜索次数更新成功")
        print(f"  用户: {email}")
        print(f"  今日已用: {updated_recent}")
        print(f"  额外搜索次数: {meta_data.get('search_bonus', 0)}")
        return True

    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='用户管理工具', formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # show-user 命令
    show_parser = subparsers.add_parser('show-user', help='显示用户信息')
    show_parser.add_argument('--email', required=True, help='用户邮箱')

    # set-record-status 命令
    status_parser = subparsers.add_parser('set-record-status', help='设置综述状态')
    status_parser.add_argument('--email', required=True, help='用户邮箱')
    status_parser.add_argument('--topic', help='综述主题（模糊匹配）')
    status_parser.add_argument('--record-id', type=int, help='综述ID')
    status_parser.add_argument('--paid', action='store_true', help='设置为已付费状态')
    status_parser.add_argument('--unpaid', action='store_true', help='设置为待付费状态')

    # update-credits 命令
    credits_parser = subparsers.add_parser('update-credits', help='更新用户额度')
    credits_parser.add_argument('--email', required=True, help='用户邮箱')
    credits_parser.add_argument('--free-credits', help='免费额度 (+1/-1/数字)')
    credits_parser.add_argument('--paid-credits', help='付费额度 (+1/-1/数字)')

    # update-search 命令
    search_parser = subparsers.add_parser('update-search', help='更新搜索次数')
    search_parser.add_argument('--email', required=True, help='用户邮箱')
    search_parser.add_argument('--bonus', help='额外搜索次数 (+5/-1/数字)')
    search_parser.add_argument('--reset', action='store_true', help='清除今日搜索记录')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'show-user':
        show_user(args.email)

    elif args.command == 'set-record-status':
        if not args.topic and not args.record_id:
            print("❌ 请指定 --topic 或 --record-id")
            return

        if args.paid and args.unpaid:
            print("❌ --paid 和 --unpaid 不能同时使用")
            return

        if not args.paid and not args.unpaid:
            print("❌ 请指定 --paid 或 --unpaid")
            return

        set_record_status(args.email, args.topic, args.record_id, paid=args.paid)

    elif args.command == 'update-credits':
        if not args.free_credits and not args.paid_credits:
            print("❌ 请指定 --free-credits 或 --paid-credits")
            return

        update_credits(args.email, args.free_credits, args.paid_credits)

    elif args.command == 'update-search':
        if not args.bonus and not args.reset:
            print("❌ 请指定 --bonus 或 --reset")
            return

        update_search(args.email, args.bonus, args.reset)


if __name__ == '__main__':
    main()
