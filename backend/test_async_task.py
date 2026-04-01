"""
测试异步任务模式
演示：提交任务 → 轮询结果
"""
import asyncio
import time
import requests


API_BASE = "http://localhost:8000"


async def test_async_task_flow():
    """测试完整的异步任务流程"""
    print("=" * 80)
    print("测试异步任务模式")
    print("=" * 80)

    # 1. 提交任务
    print("\n[1] 提交综述生成任务...")
    submit_request = {
        "topic": "基于FMEA法的Agent开发项目风险管理研究",
        "target_count": 30,
        "recent_years_ratio": 0.5,
        "english_ratio": 0.3,
        "search_years": 10,
        "max_search_queries": 6
    }

    response = requests.post(f"{API_BASE}/api/smart-generate", json=submit_request)
    result = response.json()

    if not result.get("success"):
        print(f"❌ 任务提交失败: {result.get('message')}")
        return

    task_id = result["data"]["task_id"]
    print(f"✅ 任务已提交")
    print(f"   任务ID: {task_id}")
    print(f"   轮询地址: {API_BASE}{result['data']['poll_url']}")

    # 2. 轮询任务状态
    print(f"\n[2] 开始轮询任务状态...")
    poll_count = 0
    max_polls = 120  # 最多轮询2分钟

    while poll_count < max_polls:
        poll_count += 1

        # 查询任务状态
        status_response = requests.get(f"{API_BASE}/api/tasks/{task_id}")
        status_data = status_response.json()

        if not status_data.get("success"):
            print(f"❌ 查询失败: {status_data.get('message')}")
            break

        task_info = status_data["data"]
        status = task_info["status"]
        progress = task_info.get("progress", {})

        # 显示进度
        progress_msg = progress.get("message", status)
        print(f"   [{poll_count:2d}] {progress_msg}", end="\r")

        # 检查任务状态
        if status == "completed":
            print(f"\n\n✅ 任务完成!")
            print(f"   耗时: {poll_count * 1} 秒")

            # 获取结果
            result_data = task_info.get("result")
            if result_data:
                print(f"\n[3] 综述生成结果:")
                print(f"   论文数量: {result_data.get('cited_papers_count')}")
                print(f"   统计信息: {result_data.get('statistics')}")
                print(f"   验证结果: {result_data.get('validation')}")

                # 显示部分综述内容
                review = result_data.get("review", "")
                print(f"\n   综述预览（前200字）:")
                print(f"   {review[:200]}...")

            break

        elif status == "failed":
            print(f"\n\n❌ 任务失败!")
            print(f"   错误: {task_info.get('error')}")
            break

        # 等待1秒后继续轮询
        await asyncio.sleep(1)

    if poll_count >= max_polls:
        print(f"\n\n⏱️  轮询超时（{max_polls}秒）")


async def test_multiple_tasks():
    """测试同时提交多个任务"""
    print("\n" + "=" * 80)
    print("测试多任务并发")
    print("=" * 80)

    topics = [
        "基于QFD的质量管理研究",
        "FMEA在风险管理中的应用",
    ]

    task_ids = []

    # 提交所有任务
    print(f"\n[1] 提交 {len(topics)} 个任务...")
    for topic in topics:
        submit_request = {
            "topic": topic,
            "target_count": 20,
            "recent_years_ratio": 0.5,
            "english_ratio": 0.3,
        }

        response = requests.post(f"{API_BASE}/api/smart-generate", json=submit_request)
        result = response.json()

        if result.get("success"):
            task_id = result["data"]["task_id"]
            task_ids.append(task_id)
            print(f"   ✅ {topic[:30]}... → {task_id}")
        else:
            print(f"   ❌ {topic[:30]}... → 失败")

    # 轮询所有任务
    print(f"\n[2] 轮询 {len(task_ids)} 个任务...")
    completed_count = 0
    poll_count = 0

    while completed_count < len(task_ids) and poll_count < 180:
        poll_count += 1
        completed_count = 0

        for task_id in task_ids:
            status_response = requests.get(f"{API_BASE}/api/tasks/{task_id}")
            status_data = status_response.json()

            if status_data.get("success"):
                task_info = status_data["data"]
                status = task_info["status"]
                progress = task_info.get("progress", {})

                if status in ["completed", "failed"]:
                    completed_count += 1

        status_str = f"进度: {completed_count}/{len(task_ids)} 完成"
        print(f"   [{poll_count:3d}] {status_str}", end="\r")
        await asyncio.sleep(1)

    print(f"\n\n✅ 所有任务处理完成!")


async def test_task_cleanup():
    """测试任务清理"""
    print("\n" + "=" * 80)
    print("测试任务清理")
    print("=" * 80)

    from services.task_manager import task_manager

    # 清理旧任务
    deleted = task_manager.cleanup_old_tasks(max_age_hours=0)
    print(f"\n清理了 {deleted} 个旧任务")

    # 显示当前任务数量
    print(f"当前任务数量: {len(task_manager._tasks)}")


async def main():
    """运行测试"""
    # 测试单个任务
    await test_async_task_flow()

    # 测试多任务
    # await test_multiple_tasks()

    # 测试清理
    # await test_task_cleanup()

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
