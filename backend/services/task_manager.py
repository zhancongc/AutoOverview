"""
异步任务管理服务
支持任务提交、状态查询、结果获取
支持并发限制，防止资源耗尽
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, Any, Set
from enum import Enum


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
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "progress": self.progress,
            "has_result": self.result is not None
        }


class TaskManager:
    """任务管理器（单例）"""

    _instance = None
    _tasks: Dict[str, Task] = {}

    # 并发控制
    _max_concurrent_tasks = 3  # 最大并发任务数
    _running_tasks: Set[str] = set()
    _task_semaphore: asyncio.Semaphore = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._task_semaphore = asyncio.Semaphore(cls._max_concurrent_tasks)
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
        # 重新创建信号量
        self._task_semaphore = asyncio.Semaphore(value)
        print(f"[TaskManager] 最大并发任务数: {old_value} → {value}")

    async def acquire_slot(self, task_id: str) -> bool:
        """
        获取任务执行槽位

        Returns:
            True 如果成功获取槽位，False 如果已达到最大并发数
        """
        if task_id in self._running_tasks:
            print(f"[TaskManager] 任务 {task_id} 已在运行中")
            return True

        # 尝试获取信号量
        acquired = await self._task_semaphore.acquire()

        if acquired:
            self._running_tasks.add(task_id)
            print(f"[TaskManager] 任务 {task_id} 获取执行槽位 (运行中: {len(self._running_tasks)}/{self._max_concurrent_tasks})")
            return True
        else:
            print(f"[TaskManager] 任务 {task_id} 等待槽位 (已达最大并发数: {self._max_concurrent_tasks})")
            return False

    def release_slot(self, task_id: str):
        """释放任务执行槽位"""
        if task_id in self._running_tasks:
            self._running_tasks.remove(task_id)
            self._task_semaphore.release()
            print(f"[TaskManager] 任务 {task_id} 释放槽位 (运行中: {len(self._running_tasks)}/{self._max_concurrent_tasks})")

    def get_running_count(self) -> int:
        """获取当前运行中的任务数"""
        return len(self._running_tasks)

    def create_task(self, topic: str, params: Dict, user_id: Optional[int] = None, is_paid: bool = False) -> Task:
        """创建新任务"""
        task_id = str(uuid.uuid4())[:8]  # 短ID
        task = Task(task_id, topic, params, user_id=user_id, is_paid=is_paid)
        self._tasks[task_id] = task
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

        if result is not None:
            task.result = result

        if error is not None:
            task.error = error

        if progress is not None:
            task.progress.update(progress)

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

        return len(to_delete)


# 全局任务管理器实例
task_manager = TaskManager()
