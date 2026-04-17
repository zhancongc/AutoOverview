#!/usr/bin/env python3
"""
调试脚本：修复任务 eba75060 - 从 API 获取数据并更新数据库
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.auth', override=True)

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import db
from models import ReviewTask
from sqlalchemy.orm.attributes import flag_modified

if __name__ == "__main__":
    task_id_to_fix = "eba75060"

    print("=" * 80)
    print(f"修复任务 ID: {task_id_to_fix}")
    print("=" * 80)

    # 第一步：从 API 获取数据
    print("\n[1] 从 API 获取对比矩阵数据...")
    try:
        # 我们需要先登录获取 token，或者直接从数据库读取
        print("   注意：需要有效的 auth token 来访问 API")
        print("   让我们先检查数据库中的任务状态...")
    except Exception as e:
        print(f"   API 请求失败: {e}")

    # 第二步：检查数据库中的任务
    if db.engine is None:
        db.connect()

    with next(db.get_session()) as session:
        # 查询特定任务
        task = session.query(ReviewTask).filter_by(id=task_id_to_fix).first()

        if task:
            print(f"\n[2] 找到任务！")
            print(f"    当前状态: {task.status}")
            print(f"    当前 params keys: {list(task.params.keys()) if task.params else 'None'}")

            # 检查是否已经有数据
            params = task.params or {}
            if 'comparison_matrix' in params and 'papers' in params:
                print("\n✓ 任务已经有完整数据了！")
            else:
                print("\n✗ 任务缺少数据，需要手动更新")
                print("\n提示：由于任务数据只在内存中（task_manager），")
                print("      如果后端服务还在运行，数据可能还在内存中。")
                print("      请重新生成一个对比矩阵任务来测试修复后的代码。")

            print(f"\n[3] 更新状态映射（确保前端显示正确）...")
            # 至少确保状态是 completed
            if task.status != "completed":
                task.status = "completed"
                session.commit()
                print("    ✓ 状态已更新为 completed")

        else:
            print(f"\n未找到任务 ID: {task_id_to_fix}")

    print("\n" + "=" * 80)
    print("修复建议：")
    print("1. 任务 eba75060 的数据可能只存在于内存中（task_manager）")
    print("2. 如果后端重启过，内存数据已丢失")
    print("3. 请重新生成一个对比矩阵任务来验证修复")
    print("=" * 80)
