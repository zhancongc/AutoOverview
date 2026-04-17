"""
临时脚本：回填 review_tasks 表的 user_id 字段
"""
import os
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text
from database import db

def backfill():
    """回填 user_id"""
    print("回填 review_tasks 表的 user_id 字段...")

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 查找 zhancongc@gmail.com 用户
        print("\n1. 查找用户 zhancongc@gmail.com：")
        result = session.execute(text("""
            SELECT id, email, nickname
            FROM users
            WHERE email = 'zhancongc@gmail.com'
        """))
        user = result.fetchone()

        if not user:
            print("  未找到该用户")
            return

        user_id = user[0]
        print(f"  找到用户: id={user_id}, email={user[1]}, nickname={user[2]}")

        # 查找 topic 包含"医疗失效模式"且 user_id 为 NULL 的任务
        print("\n2. 查找需要回填的任务：")
        result = session.execute(text("""
            SELECT id, topic, user_id, status, created_at
            FROM review_tasks
            WHERE topic LIKE '%医疗失效模式%'
            AND user_id IS NULL
            ORDER BY created_at DESC
        """))
        tasks = result.fetchall()

        if not tasks:
            print("  没有找到需要回填的任务")
            return

        print(f"  找到 {len(tasks)} 个任务：")
        for task in tasks:
            print(f"    - id: {task[0]}, topic: {task[1][:50]}..., created_at: {task[4]}")

        # 确认回填
        confirm = input("\n是否回填这些任务的 user_id? (y/n): ")
        if confirm.lower() != 'y':
            print("  取消回填")
            return

        # 执行回填
        print("\n3. 执行回填...")
        for task in tasks:
            session.execute(text("""
                UPDATE review_tasks
                SET user_id = :user_id
                WHERE id = :task_id
            """), {"user_id": user_id, "task_id": task[0]})
            print(f"  ✓ 已更新任务 {task[0]}")

        session.commit()
        print("\n✓ 回填完成")

        # 验证结果
        print("\n4. 验证结果：")
        result = session.execute(text("""
            SELECT id, topic, user_id, status, created_at
            FROM review_tasks
            WHERE topic LIKE '%医疗失效模式%'
            ORDER BY created_at DESC
        """))
        tasks = result.fetchall()
        for task in tasks:
            print(f"  - id: {task[0]}, user_id: {task[2]}, topic: {task[1][:50]}...")

if __name__ == "__main__":
    backfill()
