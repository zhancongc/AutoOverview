#!/usr/bin/env python3
"""
调试脚本：检查任务 eee1f720
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
    task_id_to_find = "eee1f720"

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
            print(f"Started: {task.started_at}")
            print(f"Completed: {task.completed_at}")

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
                if 'statistics' in params:
                    print("✓ 有 statistics 数据")
        else:
            print(f"\n未找到任务 ID: {task_id_to_find}")

    print("\n" + "=" * 80)
