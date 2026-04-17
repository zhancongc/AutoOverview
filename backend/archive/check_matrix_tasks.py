#!/usr/bin/env python3
"""
调试脚本：检查数据库中的对比矩阵任务
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
    print("检查 ReviewTask 表中的对比矩阵任务")
    print("=" * 80)

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 查询所有任务
        tasks = session.query(ReviewTask).order_by(ReviewTask.created_at.desc()).limit(20).all()

        print(f"\n找到 {len(tasks)} 个任务（最近20个）:\n")

        for i, task in enumerate(tasks):
            params = task.params or {}
            task_type = params.get('type', 'N/A')

            print(f"[{i+1}] Task ID: {task.id}")
            print(f"      Topic: {task.topic}")
            print(f"      User ID: {task.user_id}")
            print(f"      Status: {task.status}")
            print(f"      Type: {task_type}")
            print(f"      Created: {task.created_at}")

            if params:
                print(f"      Params keys: {list(params.keys())}")
                if 'comparison_matrix' in params:
                    print(f"      Has comparison_matrix in params: YES")
                if 'papers' in params:
                    print(f"      Has papers in params: YES")

            print()

    print("=" * 80)
