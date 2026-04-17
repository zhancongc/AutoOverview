#!/usr/bin/env python3
"""
调试脚本：检查特定的 task_id
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
    task_id_to_find = "f9b9e9f2"

    print("=" * 80)
    print(f"查找任务 ID: {task_id_to_find}")
    print("=" * 80)

    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 查询特定任务
        task = session.query(ReviewTask).filter_by(id=task_id_to_find).first()

        if task:
            print(f"\n找到任务！\n")
            print(f"Task ID: {task.id}")
            print(f"Topic: {task.topic}")
            print(f"User ID: {task.user_id}")
            print(f"Status: {task.status}")
            print(f"Created: {task.created_at}")
            print(f"Started: {task.started_at}")
            print(f"Completed: {task.completed_at}")

            params = task.params or {}
            print(f"\nParams: {params}")

            # 检查 ReviewTask 的所有字段
            print(f"\n所有字段:")
            for column in ReviewTask.__table__.columns:
                value = getattr(task, column.name)
                print(f"  {column.name}: {value}")
        else:
            print(f"\n未找到任务 ID: {task_id_to_find}")

            # 尝试模糊搜索
            print(f"\n尝试模糊搜索...")
            tasks = session.query(ReviewTask).filter(ReviewTask.id.like(f"%{task_id_to_find}%")).all()
            if tasks:
                print(f"找到 {len(tasks)} 个匹配的任务:")
                for t in tasks:
                    print(f"  - {t.id}: {t.topic}")
            else:
                print("没有找到匹配的任务")

    print("\n" + "=" * 80)
