"""
异步任务管理服务
支持任务提交、状态查询、结果获取
支持并发限制，防止资源耗尽
支持 Redis 持久化，防止重启后任务状态丢失
"""
import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum

from services.progress_messages import get_progress


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"        # 等待执行
    PROCESSING = "processing"  # 执行中
    COMPLETED = "completed"    # 完成
    FAILED = "failed"          # 失败


class Task:
    """任务对象"""

    def __init__(self, task_id: str, topic: str, params: Dict, user_id: Optional[int] = None, is_paid: bool = False):
        self.task_id = task_id
        self.topic = topic
        self.params = params
        self.user_id = user_id  # 创建任务的用户ID
        self.is_paid = is_paid  # 用户是否已付费
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict] = None
        self.error: Optional[str] = None
        self.progress: Dict[str, Any] = {}  # 进度信息

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "topic": self.topic,
            "status": self.status.value,
            "user_id": self.user_id,
            "is_paid": self.is_paid,
            "params": self.params,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "progress": self.progress,
            "has_result": self.result is not None
        }


# ==================== Redis 持久化 ====================

class TaskPersistence:
    """Redis 持久化层：将活跃任务状态写入 Redis，防止重启丢失"""

    KEY_PREFIX = "task:active:"
    INDEX_KEY = "task:active_ids"
    TTL_SECONDS = 86400  # 24 小时

    def __init__(self):
        try:
            from authkit.core.config import config as auth_config
            import redis as _redis
            self.redis_client = _redis.Redis(
                host=auth_config.REDIS_HOST,
                port=auth_config.REDIS_PORT,
                db=auth_config.REDIS_DB,
                password=auth_config.REDIS_PASSWORD,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            print("[TaskPersistence] Redis 连接成功")
        except Exception as e:
            print(f"[TaskPersistence] Redis 不可用，降级为纯内存模式: {e}")
            self.redis_client = None

    @property
    def available(self) -> bool:
        return self.redis_client is not None

    def save_task(self, task: Task):
        """持久化一个活跃任务到 Redis"""
        if not self.available:
            return
        try:
            data = {
                "task_id": task.task_id,
                "topic": task.topic,
                "params": task.params,
                "user_id": task.user_id,
                "is_paid": task.is_paid,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "progress": task.progress,
            }
            key = f"{self.KEY_PREFIX}{task.task_id}"
            pipe = self.redis_client.pipeline()
            pipe.setex(key, self.TTL_SECONDS, json.dumps(data, ensure_ascii=False))
            pipe.sadd(self.INDEX_KEY, task.task_id)
            pipe.execute()
        except Exception as e:
            print(f"[TaskPersistence] save_task 失败: {e}")

    def remove_task(self, task_id: str):
        """从 Redis 移除已结束的任务"""
        if not self.available:
            return
        try:
            key = f"{self.KEY_PREFIX}{task_id}"
            pipe = self.redis_client.pipeline()
            pipe.delete(key)
            pipe.srem(self.INDEX_KEY, task_id)
            pipe.execute()
        except Exception as e:
            print(f"[TaskPersistence] remove_task 失败: {e}")

    def update_progress(self, task_id: str, progress: dict):
        """仅更新 progress 字段（比 save_task 更轻量）"""
        if not self.available:
            return
        try:
            key = f"{self.KEY_PREFIX}{task_id}"
            raw = self.redis_client.get(key)
            if raw:
                data = json.loads(raw)
                data["progress"] = progress
                self.redis_client.setex(key, self.TTL_SECONDS, json.dumps(data, ensure_ascii=False))
        except Exception as e:
            print(f"[TaskPersistence] update_progress 失败: {e}")

    def get_all_active_tasks(self) -> List[dict]:
        """获取 Redis 中所有活跃任务的数据"""
        if not self.available:
            return []
        try:
            task_ids = self.redis_client.smembers(self.INDEX_KEY)
            results = []
            for task_id in task_ids:
                raw = self.redis_client.get(f"{self.KEY_PREFIX}{task_id}")
                if raw:
                    results.append(json.loads(raw))
                else:
                    # key 已过期但索引还在，清理孤儿条目
                    self.redis_client.srem(self.INDEX_KEY, task_id)
            return results
        except Exception as e:
            print(f"[TaskPersistence] get_all_active_tasks 失败: {e}")
            return []


# ==================== 任务管理器 ====================

class TaskManager:
    """任务管理器（单例）"""

    _instance = None
    _tasks: Dict[str, Task] = {}

    # 并发控制
    _max_concurrent_tasks = 3  # 最大并发任务数
    _running_tasks: Set[str] = set()
    _waiting_tasks: Dict[str, float] = {}  # task_id -> monotonic timestamp

    # Redis 持久化
    _persistence: Optional[TaskPersistence] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._persistence = TaskPersistence()
            print(f"[TaskManager] 初始化，最大并发任务数: {cls._max_concurrent_tasks}")
        return cls._instance

    @property
    def max_concurrent_tasks(self) -> int:
        """获取最大并发任务数"""
        return self._max_concurrent_tasks

    @max_concurrent_tasks.setter
    def max_concurrent_tasks(self, value: int):
        """设置最大并发任务数"""
        if value < 1:
            raise ValueError("max_concurrent_tasks must be at least 1")
        old_value = self._max_concurrent_tasks
        self._max_concurrent_tasks = value
        print(f"[TaskManager] 最大并发任务数: {old_value} → {value}")

    def _get_queue_position(self, task_id: str) -> int:
        """获取任务在等待队列中的位置（1-based，0 表示不在队列中）"""
        if task_id not in self._waiting_tasks:
            return 0
        sorted_waiting = sorted(self._waiting_tasks.items(), key=lambda x: x[1])
        for i, (tid, _) in enumerate(sorted_waiting):
            if tid == task_id:
                return i + 1
        return 0

    def get_queue_info(self, task_id: str) -> dict:
        """获取任务的队列信息"""
        if task_id in self._running_tasks:
            return {"status": "running", "queue_position": 0}
        if task_id in self._waiting_tasks:
            return {"status": "waiting", "queue_position": self._get_queue_position(task_id)}
        return {"status": "unknown", "queue_position": 0}

    async def acquire_slot(self, task_id: str, timeout: float = 1800) -> bool:
        """
        获取任务执行槽位（支持排队提示和超时）

        如果当前槽位已满，会自动进入等待队列并定期更新排队位置。
        等待期间每 5 秒更新一次任务进度，前端轮询时可看到排队信息。

        Args:
            task_id: 任务ID
            timeout: 最大等待时间（秒），默认 30 分钟

        Returns:
            True 如果成功获取槽位，False 如果超时
        """
        if task_id in self._running_tasks:
            print(f"[TaskManager] 任务 {task_id} 已在运行中")
            return True

        # 注册到等待队列
        self._waiting_tasks[task_id] = time.monotonic()
        queue_pos = self._get_queue_position(task_id)
        print(f"[TaskManager] 任务 {task_id} 进入等待队列 (位置: {queue_pos}, 运行中: {len(self._running_tasks)}/{self._max_concurrent_tasks})")

        try:
            deadline = time.monotonic() + timeout

            while time.monotonic() < deadline:
                # 检查是否有可用槽位
                if len(self._running_tasks) < self._max_concurrent_tasks:
                    self._running_tasks.add(task_id)
                    print(f"[TaskManager] 任务 {task_id} 获取执行槽位 (运行中: {len(self._running_tasks)}/{self._max_concurrent_tasks})")
                    return True

                # 更新排队进度（前端轮询时会读取 task.progress）
                queue_pos = self._get_queue_position(task_id)
                task = self._tasks.get(task_id)
                if task:
                    # 从任务参数中获取语言，默认为中文
                    language = task.params.get("language", "zh") if task.params else "zh"
                    progress_msg = get_progress("waiting", language, queue_pos=queue_pos)
                    task.progress = progress_msg
                    # 同步排队进度到 Redis
                    if self._persistence:
                        self._persistence.update_progress(task_id, progress_msg)

                # 等待 5 秒后重试
                await asyncio.sleep(5)

            # 超时
            print(f"[TaskManager] 任务 {task_id} 等待超时（{timeout}秒）")
            return False

        finally:
            self._waiting_tasks.pop(task_id, None)

    def release_slot(self, task_id: str):
        """释放任务执行槽位"""
        if task_id in self._running_tasks:
            self._running_tasks.remove(task_id)
            print(f"[TaskManager] 任务 {task_id} 释放槽位 (运行中: {len(self._running_tasks)}/{self._max_concurrent_tasks})")

    def get_running_count(self) -> int:
        """获取当前运行中的任务数"""
        return len(self._running_tasks)

    def get_waiting_count(self) -> int:
        """获取当前等待中的任务数"""
        return len(self._waiting_tasks)

    def create_task(self, topic: str, params: Dict, user_id: Optional[int] = None, is_paid: bool = False) -> Task:
        """创建新任务"""
        task_id = str(uuid.uuid4())[:8]  # 短ID
        task = Task(task_id, topic, params, user_id=user_id, is_paid=is_paid)
        self._tasks[task_id] = task

        # 持久化到 Redis
        if self._persistence:
            self._persistence.save_task(task)

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self._tasks.get(task_id)

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
        progress: Optional[Dict] = None
    ):
        """更新任务状态"""
        task = self._tasks.get(task_id)
        if not task:
            return

        task.status = status

        if status == TaskStatus.PROCESSING and not task.started_at:
            task.started_at = datetime.now()

        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            task.completed_at = datetime.now()
            # 释放执行槽位
            self.release_slot(task_id)
            # 终态任务从 Redis 移除（PostgreSQL 已有完整记录）
            if self._persistence:
                self._persistence.remove_task(task_id)

        if result is not None:
            task.result = result

        if error is not None:
            task.error = error

        if progress is not None:
            task.progress.update(progress)

        # 非终态变更时同步到 Redis
        if self._persistence and status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            if status == TaskStatus.PROCESSING:
                # 状态变为 PROCESSING 时全量更新
                self._persistence.save_task(task)
            elif progress is not None:
                # 仅进度更新时轻量写入
                self._persistence.update_progress(task_id, task.progress)

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_delete = [
            task_id for task_id, task in self._tasks.items()
            if task.created_at < cutoff
        ]
        for task_id in to_delete:
            del self._tasks[task_id]
            if self._persistence:
                self._persistence.remove_task(task_id)

        return len(to_delete)

    def restore_from_redis(self):
        """
        从 Redis 恢复活跃任务状态（服务器重启时调用）

        - pending 任务：恢复到内存，用户轮询可见
        - processing 任务：标记为失败（服务器重启导致中断），退还额度
        """
        if not self._persistence or not self._persistence.available:
            print("[TaskManager] Redis 不可用，跳过任务恢复")
            return

        active_tasks = self._persistence.get_all_active_tasks()
        if not active_tasks:
            print("[TaskManager] Redis 中无活跃任务需要恢复")
            return

        restored_pending = 0
        failed_interrupted = 0

        for data in active_tasks:
            task_id = data["task_id"]
            status = data.get("status", "pending")

            # 重建 Task 对象
            task = Task(
                task_id=task_id,
                topic=data["topic"],
                params=data["params"],
                user_id=data.get("user_id"),
                is_paid=data.get("is_paid", False)
            )
            task.created_at = datetime.fromisoformat(data["created_at"])
            task.started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
            task.progress = data.get("progress", {})

            if status == "pending":
                # 排队中的任务恢复到内存，保持 pending 状态
                task.status = TaskStatus.PENDING
                self._tasks[task_id] = task
                restored_pending += 1
                print(f"[TaskManager] 恢复排队任务: {task_id} ({task.topic})")

            elif status == "processing":
                # 执行中被中断，标记为失败
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                task.error = "服务器重启导致任务中断，请重新提交"
                self._tasks[task_id] = task
                failed_interrupted += 1
                print(f"[TaskManager] 中断任务标记为失败: {task_id} ({task.topic})")

                # 更新 PostgreSQL
                try:
                    from services.stage_recorder import stage_recorder
                    stage_recorder.update_task_status(
                        task_id, status="failed",
                        error_message="服务器重启导致任务中断，请重新提交",
                        completed_at=datetime.now()
                    )
                except Exception as e:
                    print(f"[TaskManager] 更新数据库失败 ({task_id}): {e}")

                # 退还额度
                user_id = data.get("user_id")
                if user_id:
                    try:
                        from main import refund_credit
                        from authkit.database import SessionLocal as AuthSessionLocal
                        if AuthSessionLocal:
                            auth_db = AuthSessionLocal()
                            try:
                                # 从 params 中获取实际扣除的 credit_cost
                                params = data.get("params", {})
                                credit_cost = params.get("credit_cost", 2)
                                refund_credit(user_id, auth_db, cost=credit_cost)
                                print(f"[TaskManager] 已退还用户 {user_id} 的 {credit_cost} 个额度")
                            finally:
                                auth_db.close()
                    except Exception as e:
                        print(f"[TaskManager] 额度退还失败 ({task_id}): {e}")

                # 从 Redis 移除（终态）
                self._persistence.remove_task(task_id)

            else:
                # 意外状态（completed/failed），直接清理
                self._persistence.remove_task(task_id)

        print(f"[TaskManager] 任务恢复完成: 恢复 {restored_pending} 个排队任务，"
              f"标记 {failed_interrupted} 个中断任务为失败")


# 全局任务管理器实例
task_manager = TaskManager()
