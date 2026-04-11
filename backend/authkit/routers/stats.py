"""
统计 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from ..models.stats import StatsBase
from ..services.stats_service import StatsService

router = APIRouter(prefix="/api/stats", tags=["统计"])


# 数据库依赖（需要在主应用中提供）
_default_get_db = None
_shared_redis_client = None


def get_db():
    """获取数据库会话（需要在主应用中实现）"""
    global _default_get_db
    if _default_get_db is not None:
        yield from _default_get_db()
        return
    raise NotImplementedError("请在主应用中实现 set_get_db() 函数")


def set_get_db(get_db_func):
    """设置数据库依赖（由主应用调用）"""
    global _default_get_db
    _default_get_db = get_db_func


def set_redis_client(redis_client):
    """设置共享 Redis 客户端"""
    global _shared_redis_client
    _shared_redis_client = redis_client


def get_stats_service(db: Session = Depends(get_db)) -> StatsService:
    """获取统计服务"""
    return StatsService(db, redis_client=_shared_redis_client)


@router.get("/overview")
async def get_stats_overview(
    stats_service: StatsService = Depends(get_stats_service)
):
    """
    获取网站统计概览

    返回：
    - total_visits: 总访问量
    - total_registers: 总注册量
    - today_visits: 今日访问量
    - today_registers: 今日注册量
    """
    stats = stats_service.get_total_stats()
    return {
        "success": True,
        "data": stats
    }


@router.get("/daily")
async def get_daily_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    stats_service: StatsService = Depends(get_stats_service)
):
    """
    获取日期范围统计数据

    参数：
    - start_date: 开始日期 (YYYY-MM-DD)，默认最近7天
    - end_date: 结束日期 (YYYY-MM-DD)，默认今天
    """
    from datetime import datetime, timedelta

    if not end_date:
        end_date = datetime.now().date().isoformat()
    if not start_date:
        start_date = (datetime.now().date() - timedelta(days=7)).isoformat()

    stats = stats_service.get_stats_by_date_range(start_date, end_date)
    return {
        "success": True,
        "data": {
            "start_date": start_date,
            "end_date": end_date,
            "stats": stats
        }
    }
