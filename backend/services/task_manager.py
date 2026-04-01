"""
异步任务管理服务
支持任务提交、状态查询、结果获取
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"        # 等待执行
    PROCESSING = "processing"  # 执行中
    COMPLETED = "completed"    # 完成
    FAILED = "failed"          # 失败


class Task:
    """任务对象"""

    def __init__(self, task_id: str, topic: str, params: Dict):
        self.task_id = task_id
        self.topic = topic
        self.params = params
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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_task(self, topic: str, params: Dict) -> Task:
        """创建新任务"""
        task_id = str(uuid.uuid4())[:8]  # 短ID
        task = Task(task_id, topic, params)
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
