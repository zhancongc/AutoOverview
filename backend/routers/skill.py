"""
Danmo Scholar Skill API 路由

提供三个核心功能：
1. /api/skill/search - 学术文献搜索
2. /api/skill/matrix - 生成文献对比矩阵
3. /api/skill/review - 生成文献综述

供 Coze / Dify 等 Agent 平台调用。
需要从 http://localhost:3006/settings 获取 API Token。
"""
import os
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import db, get_db
from services.task_manager import TaskManager, TaskStatus, task_manager
from services.review_task_executor import ReviewTaskExecutor

router = APIRouter(prefix="/api/skill", tags=["skill"])

security = HTTPBearer(auto_error=False)

# Token-based 限速（1秒1次）
_token_last_request = {}  # token -> last timestamp (seconds)


def _check_token_rate_limit(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """检查 token 频率限制：1秒最多1次请求"""
    if not credentials:
        return  # 未登录不限速
    token = credentials.credentials
    now = time.time()
    last = _token_last_request.get(token, 0)
    if now - last < 1.0:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试（每个 token 1秒最多1次请求）")
    _token_last_request[token] = now


def _get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[int]:
    if not credentials:
        return None
    from authkit.core.security import decode_access_token
    payload = decode_access_token(credentials.credentials)
    if payload:
        uid = payload.get("sub")
        return int(uid) if uid else None
    return None


# ==================== 复用原有接口的逻辑 ====================
# 从 main.py 导入需要的函数
def _check_daily_search_limit(user_id: int, auth_db):
    """复用每日搜索次数检查逻辑"""
    from main import check_daily_search_limit
    return check_daily_search_limit(user_id, auth_db)


def _check_and_deduct_credit(user_id: int, auth_db, cost: int, detail: str = None):
    """复用积分扣除逻辑"""
    from main import check_and_deduct_credit
    return check_and_deduct_credit(user_id, auth_db, cost=cost, detail=detail)


def _refund_credit(user_id: int, auth_db, cost: int, detail: str = None):
    """复用积分退还逻辑"""
    from main import refund_credit
    return refund_credit(user_id, auth_db, cost=cost, detail=detail)


# ==================== 通用响应模型 ====================
class SkillBaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


# ==================== 1. 学术搜索 API ====================
class SkillSearchRequest(BaseModel):
    query: str = Field(..., description="搜索关键词", min_length=1)
    max_papers: int = Field(30, description="返回文献数量", ge=10, le=100)
    years: int = Field(10, description="搜索最近多少年的文献", ge=1, le=50)


class SkillSearchResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/search", response_model=SkillSearchResponse)
async def skill_search(
    request: SkillSearchRequest,
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_db),
    user_id: Optional[int] = Depends(_get_user_id),
    _rate_limit: None = Depends(_check_token_rate_limit),
):
    """
    学术文献搜索（复用原有逻辑）

    必须登录（Bearer Token）。
    不扣积分，但有每日搜索次数限制（与网站一致）。
    """
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="请先登录。访问 http://localhost:3006 注册，在 /settings 页面获取 API Token。"
        )

    # 每日搜索次数限制检查（复用原有逻辑）
    from authkit.database import SessionLocal as AuthSessionLocal
    if AuthSessionLocal:
        auth_db = AuthSessionLocal()
        try:
            allowed, remaining, limit, bonus = _check_daily_search_limit(user_id, auth_db)
            if not allowed:
                return SkillSearchResponse(
                    success=False,
                    message="搜索次数已用完，购买套餐可获得更多搜索次数"
                )
        finally:
            auth_db.close()

    try:
        from services.stage_recorder import stage_recorder

        # 创建一个 ReviewTask（用于搜索）
        task = task_manager.create_task(
            topic=request.query,
            params={
                "type": "search_only",
                "target_count": request.max_papers,
                "search_years": request.years,
                "source": "skill_api",
            },
            user_id=user_id,
            is_paid=False,
        )

        # 创建数据库记录
        stage_recorder.create_task(
            task_id=task.task_id,
            topic=request.query,
            params=task.params,
            user_id=user_id
        )

        # 异步执行搜索（复用 ReviewTaskExecutor 的 search_only 方法）
        async def run_search():
            executor = ReviewTaskExecutor()
            with next(db.get_session()) as task_session:
                await executor.search_only(task.task_id, task_session)

        import asyncio
        asyncio.create_task(run_search())

        return SkillSearchResponse(
            success=True,
            message="搜索任务已提交，请轮询获取结果",
            data={
                "task_id": task.task_id,
                "topic": request.query,
                "status": TaskStatus.PENDING.value,
                "poll_url": f"/api/search-history/{task.task_id}",
            },
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return SkillSearchResponse(success=False, message=f"搜索失败: {str(e)}")


# ==================== 2. 对比矩阵 API ====================
class SkillMatrixRequest(BaseModel):
    query: str = Field(..., description="研究主题", min_length=1)
    language: str = Field("zh", description="矩阵语言：zh 或 en")
    max_papers: int = Field(30, description="目标文献数量", ge=10, le=100)
    reuse_task_id: str = Field("", description="复用已有搜索任务的ID（可选）")


class SkillMatrixResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/matrix", response_model=SkillMatrixResponse)
async def skill_matrix(
    request: SkillMatrixRequest,
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_db),
    user_id: Optional[int] = Depends(_get_user_id),
    _rate_limit: None = Depends(_check_token_rate_limit),
):
    """
    生成文献对比矩阵（消耗1积分，复用原有逻辑）

    必须登录（Bearer Token）。
    返回 task_id，通过 GET /api/tasks/{task_id} 轮询进度，
    完成后通过 GET /api/comparison-matrix/{task_id} 获取矩阵。
    """
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="请先登录。访问 http://localhost:3006 注册，在 /settings 页面获取 API Token。"
        )

    # 检查 API 配置
    if not os.getenv("DEEPSEEK_API_KEY"):
        return SkillMatrixResponse(success=False, message="服务暂时不可用，请稍后重试")

    # 扣积分（复用原有逻辑）
    from authkit.database import SessionLocal as AuthSessionLocal

    is_paid = False
    credit_cost = 1

    if AuthSessionLocal:
        auth_db = AuthSessionLocal()
        try:
            usage_error, used_paid = _check_and_deduct_credit(
                user_id, auth_db, cost=credit_cost, detail=f"对比矩阵(Skill): {request.query}"
            )
            if usage_error:
                return SkillMatrixResponse(
                    success=False,
                    message=f"{usage_error}。请访问 http://localhost:3006/#pricing 充值。"
                )
            is_paid = used_paid
        finally:
            auth_db.close()

    try:
        from services.stage_recorder import stage_recorder

        task = task_manager.create_task(
            topic=request.query,
            params={
                "type": "comparison_matrix_only",
                "language": request.language,
                "reuse_task_id": request.reuse_task_id,
                "target_count": request.max_papers,
                "credit_cost": credit_cost,
                "source": "skill_api",
            },
            user_id=user_id,
            is_paid=is_paid,
        )

        # 创建数据库记录
        stage_recorder.create_task(
            task_id=task.task_id,
            topic=request.query,
            params=task.params,
            user_id=user_id
        )

        # 启动后台任务（复用原有逻辑）
        async def run_task():
            executor = ReviewTaskExecutor()
            with next(db.get_session()) as task_session:
                await executor.execute_comparison_matrix_only(
                    task.task_id,
                    task_session,
                    request.reuse_task_id,
                    request.language
                )

        import asyncio
        asyncio.create_task(run_task())

        return SkillMatrixResponse(
            success=True,
            message="对比矩阵任务已提交，请轮询获取结果",
            data={
                "task_id": task.task_id,
                "topic": request.query,
                "status": TaskStatus.PENDING.value,
                "poll_url": f"/api/tasks/{task.task_id}",
                "matrix_url": f"/api/comparison-matrix/{task.task_id}",
            },
        )

    except Exception as e:
        # 任务创建失败，退回积分
        if AuthSessionLocal:
            try:
                auth_db = AuthSessionLocal()
                _refund_credit(user_id, auth_db, cost=credit_cost, detail=f"matrix_refund: {request.query}")
            finally:
                auth_db.close()
        import traceback
        traceback.print_exc()
        return SkillMatrixResponse(success=False, message=f"任务提交失败: {str(e)}")


# ==================== 3. 文献综述 API ====================
class SkillReviewRequest(BaseModel):
    query: str = Field(..., description="研究主题", min_length=1)
    language: str = Field("zh", description="综述语言：zh 或 en")
    max_papers: int = Field(30, description="目标文献数量", ge=10, le=100)
    reuse_task_id: str = Field("", description="复用已有搜索任务的ID（可选）")


class SkillReviewResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/review", response_model=SkillReviewResponse)
async def skill_review(
    request: SkillReviewRequest,
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_db),
    user_id: Optional[int] = Depends(_get_user_id),
    _rate_limit: None = Depends(_check_token_rate_limit),
):
    """
    生成文献综述（消耗2积分，复用原有逻辑）

    必须登录（Bearer Token）。
    返回 task_id，通过 GET /api/tasks/{task_id} 轮询进度，
    完成后通过 GET /api/tasks/{task_id}/review 获取综述。
    """
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="请先登录。访问 http://localhost:3006 注册，在 /settings 页面获取 API Token。"
        )

    # 检查 API 配置
    if not os.getenv("DEEPSEEK_API_KEY"):
        return SkillReviewResponse(success=False, message="服务暂时不可用，请稍后重试")

    # 扣积分（复用原有逻辑）
    from authkit.database import SessionLocal as AuthSessionLocal

    is_paid = False
    credit_cost = 2

    if AuthSessionLocal:
        auth_db = AuthSessionLocal()
        try:
            usage_error, used_paid = _check_and_deduct_credit(
                user_id, auth_db, cost=credit_cost, detail=f"综述(Skill): {request.query}"
            )
            if usage_error:
                return SkillReviewResponse(
                    success=False,
                    message=f"{usage_error}。请访问 http://localhost:3006/#pricing 充值。"
                )
            is_paid = used_paid
        finally:
            auth_db.close()

    try:
        from services.stage_recorder import stage_recorder

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
                "source": "skill_api",
                "reuse_task_id": request.reuse_task_id,
            },
            user_id=user_id,
            is_paid=is_paid,
        )

        # 创建数据库记录
        stage_recorder.create_task(
            task_id=task.task_id,
            topic=request.query,
            params=task.params,
            user_id=user_id
        )

        # 启动后台任务（复用原有逻辑）
        async def run_task():
            executor = ReviewTaskExecutor()
            with next(db.get_session()) as task_session:
                await executor.execute_task(task.task_id, task_session)

        import asyncio
        asyncio.create_task(run_task())

        return SkillReviewResponse(
            success=True,
            message="综述任务已提交，请轮询获取结果",
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
                _refund_credit(user_id, auth_db, cost=credit_cost, detail=f"review_refund: {request.query}")
            finally:
                auth_db.close()
        import traceback
        traceback.print_exc()
        return SkillReviewResponse(success=False, message=f"任务提交失败: {str(e)}")
