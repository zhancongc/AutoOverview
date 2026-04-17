#!/usr/bin/env python3
"""
调试脚本：检查所有对比矩阵任务
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
    print("=" * 80)
    print("检查所有对比矩阵任务")
    print("=" * 80)

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 查询所有任务
        all_tasks = session.query(ReviewTask).order_by(ReviewTask.created_at.desc()).all()

        print(f"\n数据库中共有 {len(all_tasks)} 个 ReviewTask 记录\n")

        matrix_count = 0
        for i, task in enumerate(all_tasks):
            params = task.params or {}
            task_type = params.get('type', 'N/A')

            if task_type == 'comparison_matrix_only':
                matrix_count += 1
                print(f"[{matrix_count}] Task ID: {task.id}")
                print(f"      Topic: {task.topic}")
                print(f"      User ID: {task.user_id}")
                print(f"      Status: {task.status}")
                print(f"      Created: {task.created_at}")

                if 'comparison_matrix' in params:
                    print(f"      ✓ 有 comparison_matrix 数据")
                if 'papers' in params:
                    print(f"      ✓ 有 papers 数据")
                print()

        if matrix_count == 0:
            print("数据库中没有找到任何对比矩阵任务！")
            print("\n这是因为之前的代码没有将对比矩阵任务写入数据库。")
            print("历史任务无法恢复，因为它们从未被保存到数据库中。")

    print("=" * 80)
