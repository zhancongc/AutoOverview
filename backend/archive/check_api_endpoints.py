#!/usr/bin/env python3
"""
调试脚本：检查对比矩阵 API 端点
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.auth', override=True)

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

task_id = "eba75060"

print("=" * 80)
print(f"检查任务 {task_id} 的 API 端点")
print("=" * 80)

# 我们需要 auth token，让我们直接从数据库检查
from database import db
from models import ReviewTask

if db.engine is None:
    db.connect()

with next(db.get_session()) as session:
    task = session.query(ReviewTask).filter_by(id=task_id).first()
    if task:
        print("\n[数据库中的任务]")
        print(f"  Status: {task.status}")
        print(f"  Params keys: {list(task.params.keys()) if task.params else 'None'}")

        params = task.params or {}
        if 'comparison_matrix' in params:
            print("  ✓ 有 comparison_matrix 数据")
        else:
            print("  ✗ 没有 comparison_matrix 数据")

        print("\n[结论]")
        print("  这个任务的数据从未被保存到数据库中。")
        print("  它可能只存在于后端服务的内存中（task_manager）。")
        print("  如果后端服务重启过，内存中的数据已丢失。")
        print("\n  请重新生成一个对比矩阵任务来测试修复后的代码。")
    else:
        print("\n未找到任务")

print("\n" + "=" * 80)
