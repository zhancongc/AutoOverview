#!/usr/bin/env python3
"""
调试脚本：检查新生成的任务
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

if __name__ == "__main__":
    task_id_to_find = "4a573b85"

    print("=" * 80)
    print(f"查找任务 ID: {task_id_to_find}")
    print("=" * 80)

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 查询特定任务
        task = session.query(ReviewTask).filter_by(id=task_id_to_find).first()

        if task:
            print(f"\n✓ 找到任务！\n")
            print(f"Task ID: {task.id}")
            print(f"Topic: {task.topic}")
            print(f"User ID: {task.user_id}")
            print(f"Status: {task.status}")
            print(f"Created: {task.created_at}")

            params = task.params or {}
            print(f"\nParams: {params}")

            task_type = params.get('type', 'N/A')
            print(f"Task Type: {task_type}")

            if task_type == 'comparison_matrix_only':
                print("\n✓ 这是对比矩阵任务！")
                if 'comparison_matrix' in params:
                    print("✓ 有 comparison_matrix 数据")
                if 'papers' in params:
                    print("✓ 有 papers 数据")

            # 检查所有用户的任务
            print(f"\n检查该用户的所有任务...")
            if task.user_id:
                user_tasks = session.query(ReviewTask).filter(ReviewTask.user_id == task.user_id).order_by(ReviewTask.created_at.desc()).limit(10).all()
                print(f"\n用户 {task.user_id} 的最近任务:")
                for t in user_tasks:
                    p = t.params or {}
                    tt = p.get('type', 'N/A')
                    print(f"  - {t.id}: {t.topic[:40]}... (type: {tt}, status: {t.status})")
        else:
            print(f"\n未找到任务 ID: {task_id_to_find}")

            # 查看最近的任务
            print(f"\n查看最近的任务...")
            recent_tasks = session.query(ReviewTask).order_by(ReviewTask.created_at.desc()).limit(10).all()
            print(f"\n最近 10 个任务:")
            for t in recent_tasks:
                p = t.params or {}
                tt = p.get('type', 'N/A')
                print(f"  - {t.id}: {t.topic[:40]}... (type: {tt}, status: {t.status})")

    print("\n" + "=" * 80)
