"""
统计服务 - 支持 Redis 缓存
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models.stats import SiteStats, VisitLog

logger = logging.getLogger(__name__)


class StatsService:
    """统计服务"""

    def __init__(self, db: Session, redis_client=None):
        self.db = db
        self.redis_client = redis_client

    def get_today_stats(self) -> dict:
        """获取今日统计数据（优先从 Redis）"""
        today = date.today().isoformat()

        # 优先从 Redis 获取
        if self.redis_client:
            visit_key = f"stats:visits:{today}"
            visits = self.redis_client.get(visit_key)
            if visits:
                visits = int(visits)
            else:
                visits = 0

            # 注册量从数据库获取（因为注册量直接写数据库）
            stats = self.db.query(SiteStats).filter_by(stat_date=today).first()
            registers = stats.register_count if stats else 0

            return {
                "stat_date": today,
                "visit_count": visits,
                "register_count": registers
            }

        # 降级到数据库
        stats = self.db.query(SiteStats).filter_by(stat_date=today).first()
        if not stats:
            return {
                "stat_date": today,
                "visit_count": 0,
                "register_count": 0
            }
        return stats.to_dict()

    def increment_visit(self, ip_address: str = None, user_agent: str = None, path: str = None, user_id: int = None):
        """
        增加访问量（直接调用，用于非中间件场景）

        注意：中间件场景应使用 Redis，避免频繁写数据库
        """
        try:
            # 如果有 Redis，直接写 Redis
            if self.redis_client:
                today = date.today().isoformat()
                visit_key = f"stats:visits:{today}"
                self.redis_client.incr(visit_key)
                self.redis_client.expire(visit_key, 86400 * 7)
                return

            # 降级到数据库
            stats = self.db.query(SiteStats).filter_by(stat_date=date.today().isoformat()).first()
            if not stats:
                stats = SiteStats(stat_date=date.today().isoformat(), visit_count=0, register_count=0)
                self.db.add(stats)
            stats.visit_count += 1
            self.db.commit()

            logger.debug(f"[Stats] 访问量+1")
        except Exception as e:
            logger.error(f"[Stats] 更新访问量失败: {e}")
            self.db.rollback()

    def increment_register(self):
        """增加注册量"""
        try:
            today = date.today().isoformat()
            stats = self.db.query(SiteStats).filter_by(stat_date=today).first()
            if not stats:
                stats = SiteStats(stat_date=today, visit_count=0, register_count=0)
                self.db.add(stats)
            stats.register_count += 1
            self.db.commit()
            logger.debug(f"[Stats] 注册量+1: {today}, 总计: {stats.register_count}")
        except Exception as e:
            logger.error(f"[Stats] 更新注册量失败: {e}")
            self.db.rollback()

    def get_stats_by_date_range(self, start_date: str, end_date: str) -> list:
        """获取指定日期范围的统计数据"""
        result = []

        # 如果有 Redis，优先从 Redis 获取访问量
        if self.redis_client:
            current = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)

            while current <= end:
                date_str = current.isoformat()
                visit_key = f"stats:visits:{date_str}"
                visits = self.redis_client.get(visit_key)
                visits = int(visits) if visits else 0

                # 注册量从数据库获取
                db_stats = self.db.query(SiteStats).filter_by(stat_date=date_str).first()
                registers = db_stats.register_count if db_stats else 0

                result.append({
                    "stat_date": date_str,
                    "visit_count": visits,
                    "register_count": registers
                })

                current += timedelta(days=1)

            return result

        # 降级到数据库
        stats = self.db.query(SiteStats).filter(
            and_(
                SiteStats.stat_date >= start_date,
                SiteStats.stat_date <= end_date
            )
        ).order_by(SiteStats.stat_date).all()
        return [s.to_dict() for s in stats]

    def get_total_stats(self) -> dict:
        """获取总统计（累计）"""
        # 如果有 Redis，计算总访问量
        if self.redis_client:
            total_visits = 0
            # 获取最近 7 天的访问量
            for i in range(7):
                date_str = (date.today() - timedelta(days=i)).isoformat()
                visit_key = f"stats:visits:{date_str}"
                visits = self.redis_client.get(visit_key)
                if visits:
                    total_visits += int(visits)

            # 加上数据库中的历史数据
            db_visits = self.db.query(func.sum(SiteStats.visit_count)).scalar() or 0
            total_visits += db_visits
        else:
            total_visits = self.db.query(func.sum(SiteStats.visit_count)).scalar() or 0

        # 总注册量
        total_registers = self.db.query(func.sum(SiteStats.register_count)).scalar() or 0

        # 今日统计
        today_stats = self.get_today_stats()

        return {
            "total_visits": total_visits,
            "total_registers": total_registers,
            "today_visits": today_stats.get("visit_count", 0),
            "today_registers": today_stats.get("register_count", 0)
        }
