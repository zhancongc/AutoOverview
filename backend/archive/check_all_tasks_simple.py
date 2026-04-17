#!/usr/bin/env python3
"""
调试脚本：检查所有任务
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
    print("检查所有任务")
    print("=" * 80)

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 获取所有任务
        tasks = session.query(ReviewTask).order_by(ReviewTask.created_at.desc()).limit(50).all()

        print(f"\n共有 {len(tasks)} 个任务:\n")

        for task in tasks:
            params = task.params or {}
            task_type = params.get('type', 'N/A')
            print(f"Task ID: {task.id}")
            print(f"  User ID: {task.user_id}")
            print(f"  Type: {task_type}")
            print(f"  Topic: {task.topic}")
            print(f"  Status: {task.status}")
            if params:
                print(f"  Params keys: {list(params.keys())}")
            print()

    print("=" * 80)
