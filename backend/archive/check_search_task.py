"""
临时脚本：检查搜索任务
"""
import os
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text
from database import db

def check():
    """检查搜索任务"""
    print("检查搜索任务...")

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 查找 topic 包含"医疗失效模式"的任务
        print("\n1. 查找包含特定 topic 的任务：")
        result = session.execute(text("""
            SELECT id, topic, user_id, status, created_at, params
            FROM review_tasks
            WHERE topic LIKE '%医疗失效模式%'
            ORDER BY created_at DESC
            LIMIT 5
        """))
        rows = result.fetchall()

        if rows:
            for row in rows:
                print(f"  - id: {row[0]}")
                print(f"    topic: {row[1]}")
                print(f"    user_id: {row[2]}")
                print(f"    status: {row[3]}")
                print(f"    created_at: {row[4]}")
                print(f"    params: {row[5]}")
                print()
        else:
            print("  没有找到相关任务")

        # 查看最近的 search_only 任务
        print("\n2. 最近的 search_only 任务：")
        result = session.execute(text("""
            SELECT id, topic, user_id, status, created_at
            FROM review_tasks
            WHERE params::text LIKE '%%search_only%%'
            ORDER BY created_at DESC
            LIMIT 10
        """))
        rows = result.fetchall()

        if rows:
            for row in rows:
                print(f"  - [{row[4]}] id={row[0]}, user_id={row[2]}, topic={row[1][:50]}...")
        else:
            print("  没有找到 search_only 任务")

        # 查看用户信息
        print("\n3. 用户信息（zhancongc@gmail.com）：")
        result = session.execute(text("""
            SELECT id, email, nickname
            FROM authkit_users
            WHERE email = 'zhancongc@gmail.com'
        """))
        rows = result.fetchall()

        if rows:
            for row in rows:
                print(f"  - id: {row[0]}, email: {row[1]}, nickname: {row[2]}")
        else:
            print("  没有找到该用户")

if __name__ == "__main__":
    check()
