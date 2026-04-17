#!/usr/bin/env python3
"""
调试脚本：检查所有用户的任务
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.auth', override=True)

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import db
from models import ReviewTask
from authkit.models import User

if __name__ == "__main__":
    print("=" * 80)
    print("检查所有用户和他们的任务")
    print("=" * 80)

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        from authkit.database import SessionLocal as AuthSessionLocal
        auth_db = AuthSessionLocal()

        try:
            # 获取所有用户
            users = auth_db.query(User).all()
            print(f"\n共有 {len(users)} 个用户:\n")

            for user in users:
                print(f"用户 ID: {user.id}, 邮箱: {user.email}")

                # 获取该用户的所有任务
                tasks = session.query(ReviewTask).filter(ReviewTask.user_id == user.id).order_by(ReviewTask.created_at.desc()).all()

                if tasks:
                    print(f"  任务数量: {len(tasks)}")
                    for task in tasks:
                        params = task.params or {}
                        task_type = params.get('type', 'N/A')
                        print(f"    - Task ID: {task.id}, Type: {task_type}, Topic: {task.topic[:50]}...")

                        # 如果是对比矩阵任务，显示更多信息
                        if task_type == 'comparison_matrix_only':
                            print(f"      ✓ 这是对比矩阵任务！")
                            if params:
                                print(f"      Params keys: {list(params.keys())}")
                else:
                    print(f"  没有任务")
                print()

        finally:
            auth_db.close()

    print("=" * 80)
