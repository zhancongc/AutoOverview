#!/usr/bin/env python3
"""
调试脚本：检查最新的任务
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
    print("检查最新的任务")
    print("=" * 80)

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 查询最新任务
        tasks = session.query(ReviewTask).order_by(ReviewTask.created_at.desc()).limit(15).all()

        print(f"\n最近 15 个任务:\n")

        for i, task in enumerate(tasks):
            params = task.params or {}
            task_type = params.get('type', 'N/A')
            print(f"[{i+1}] Task ID: {task.id}")
            print(f"      Topic: {task.topic[:50]}...")
            print(f"      User ID: {task.user_id}")
            print(f"      Type: {task_type}")
            print(f"      Status: {task.status}")
            print(f"      Created: {task.created_at}")

            if task_type == 'comparison_matrix_only':
                print(f"      ✓ 这是对比矩阵任务！")
                if 'comparison_matrix' in params:
                    print(f"      ✓ 有 comparison_matrix 数据")
                if 'papers' in params:
                    print(f"      ✓ 有 papers 数据")
            print()

    print("=" * 80)
