"""
Coze Skill API 路由

提供 /api/skill/research 接口，供 Coze / Dify 等 Agent 平台调用。
内部复用 smart-generate 的完整流程（搜索 + 生成 + 校验）。
"""
import os
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import db, get_db
from services.task_manager import TaskManager, TaskStatus, task_manager
from services.review_task_executor import ReviewTaskExecutor

router = APIRouter(prefix="/api/skill", tags=["skill"])

security = HTTPBearer(auto_error=False)


def _get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[int]:
    if not credentials:
        return None
    from authkit.core.security import decode_access_token
    payload = decode_access_token(credentials.credentials)
    if payload:
        uid = payload.get("sub")
        return int(uid) if uid else None
    return None


class SkillResearchRequest(BaseModel):
    query: str = Field(..., description="研究主题", min_length=1)
    language: str = Field("zh", description="综述语言：zh 或 en")
    max_papers: int = Field(30, description="目标文献数量", ge=10, le=100)


class SkillResearchResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/research", response_model=SkillResearchResponse)
async def skill_research(
    request: SkillResearchRequest,
    db_session: Session = Depends(get_db),
    user_id: Optional[int] = Depends(_get_user_id),
):
    """
    Coze Skill 接口：提交文献综述生成任务。

    必须登录（Bearer Token），扣 2 积分。
    返回 task_id，通过 GET /api/tasks/{task_id} 轮询进度，
    完成后通过 GET /api/tasks/{task_id}/review 获取综述。
    """
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="请先登录。访问 https://scholar.danmo.tech 注册，在个人中心获取 API Token。"
        )

    # 检查 API 配置
    if not os.getenv("DEEPSEEK_API_KEY"):
        return SkillResearchResponse(success=False, message="服务暂时不可用，请稍后重试")

    # 扣积分
    from authkit.database import SessionLocal as AuthSessionLocal

    is_paid = False
    credit_cost = 2

    if AuthSessionLocal:
        auth_db = AuthSessionLocal()
        try:
            from main import check_and_deduct_credit
            usage_error, used_paid = check_and_deduct_credit(user_id, auth_db, cost=credit_cost)
            if usage_error:
                return SkillResearchResponse(
                    success=False,
                    message=f"{usage_error}。请访问 https://scholar.danmo.tech 充值。"
                )
            is_paid = used_paid
        finally:
            auth_db.close()

    try:
        task = task_manager.create_task(
            topic=request.query,
            params={
                "research_direction_id": "",
                "research_direction": "",
                "language": request.language,
                "target_count": request.max_papers,
                "recent_years_ratio": 0.5,
                "english_ratio": 0.0,
                "search_years": 10,
                "max_search_queries": 8,
                "credit_cost": credit_cost,
                "source": "coze_skill",
            },
            user_id=user_id,
            is_paid=is_paid,
        )

        async def run_task():
            executor = ReviewTaskExecutor()
            with next(db.get_session()) as task_session:
                await executor.execute_task(task.task_id, task_session)

        asyncio.create_task(run_task())

        return SkillResearchResponse(
            success=True,
            message="任务已提交，请轮询获取结果",
            data={
                "task_id": task.task_id,
                "topic": request.query,
                "status": TaskStatus.PENDING.value,
                "poll_url": f"/api/tasks/{task.task_id}",
                "review_url": f"/api/tasks/{task.task_id}/review",
            },
        )

    except Exception as e:
        # 任务创建失败，退回积分
        if AuthSessionLocal:
            try:
                auth_db = AuthSessionLocal()
                from main import refund_credit
                refund_credit(user_id, auth_db, cost=credit_cost)
            finally:
                auth_db.close()
        import traceback
        traceback.print_exc()
        return SkillResearchResponse(success=False, message=f"任务提交失败: {str(e)}")
