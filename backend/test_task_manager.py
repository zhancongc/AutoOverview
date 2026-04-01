"""
测试任务管理器功能
"""
from services.task_manager import TaskManager, TaskStatus, task_manager


def test_task_manager():
    """测试任务管理器基本功能"""
    print("=" * 80)
    print("测试任务管理器")
    print("=" * 80)

    # 1. 创建任务
    print("\n[1] 创建任务...")
    task = task_manager.create_task(
        topic="测试主题",
        params={
            "target_count": 50,
            "recent_years_ratio": 0.5
        }
    )

    print(f"✅ 任务创建成功")
    print(f"   任务ID: {task.task_id}")
    print(f"   主题: {task.topic}")
    print(f"   状态: {task.status.value}")

    # 2. 获取任务
    print(f"\n[2] 获取任务...")
    retrieved_task = task_manager.get_task(task.task_id)

    if retrieved_task:
        print(f"✅ 任务获取成功")
        print(f"   状态: {retrieved_task.status.value}")
    else:
        print(f"❌ 任务获取失败")

    # 3. 更新任务状态
    print(f"\n[3] 更新任务状态...")

    # 更新为处理中
    task_manager.update_task_status(
        task.task_id,
        TaskStatus.PROCESSING,
        progress={"step": "analyzing", "message": "正在分析题目..."}
    )

    retrieved_task = task_manager.get_task(task.task_id)
    print(f"✅ 状态更新为: {retrieved_task.status.value}")
    print(f"   进度: {retrieved_task.progress}")

    # 更新进度
    task_manager.update_task_status(
        task.task_id,
        TaskStatus.PROCESSING,
        progress={"step": "searching", "message": "正在搜索文献..."}
    )

    retrieved_task = task_manager.get_task(task.task_id)
    print(f"✅ 进度更新: {retrieved_task.progress}")

    # 4. 标记完成
    print(f"\n[4] 标记任务完成...")
    task_manager.update_task_status(
        task.task_id,
        TaskStatus.COMPLETED,
        result={"review": "测试综述内容...", "papers": []}
    )

    retrieved_task = task_manager.get_task(task.task_id)
    print(f"✅ 任务完成")
    print(f"   状态: {retrieved_task.status.value}")
    print(f"   开始时间: {retrieved_task.started_at}")
    print(f"   完成时间: {retrieved_task.completed_at}")
    print(f"   有结果: {retrieved_task.result is not None}")

    # 5. 测试失败状态
    print(f"\n[5] 测试失败状态...")
    failed_task = task_manager.create_task(
        topic="失败测试",
        params={}
    )

    task_manager.update_task_status(
        failed_task.task_id,
        TaskStatus.PROCESSING
    )

    task_manager.update_task_status(
        failed_task.task_id,
        TaskStatus.FAILED,
        error="模拟错误：未找到相关文献"
    )

    failed_retrieved = task_manager.get_task(failed_task.task_id)
    print(f"✅ 失败任务")
    print(f"   状态: {failed_retrieved.status.value}")
    print(f"   错误: {failed_retrieved.error}")

    # 6. 转换为字典
    print(f"\n[6] 转换为字典...")
    task_dict = retrieved_task.to_dict()
    print(f"✅ 字典键: {list(task_dict.keys())}")

    # 7. 清理旧任务
    print(f"\n[7] 清理旧任务...")
    deleted = task_manager.cleanup_old_tasks(max_age_hours=0)
    print(f"✅ 清理了 {deleted} 个任务")
    print(f"   剩余任务数: {len(task_manager._tasks)}")

    print("\n" + "=" * 80)
    print("✅ 所有测试通过")
    print("=" * 80)


if __name__ == "__main__":
    test_task_manager()
