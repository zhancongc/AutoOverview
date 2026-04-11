"""
统计服务
"""
import logging
from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.stats import SiteStats, VisitLog

logger = logging.getLogger(__name__)


class StatsService:
    """统计服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_today_stats(self) -> SiteStats:
        """获取今日统计数据"""
        today = date.today().isoformat()
        stats = self.db.query(SiteStats).filter_by(stat_date=today).first()
        if not stats:
            stats = SiteStats(stat_date=today, visit_count=0, register_count=0)
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)
        return stats

    def increment_visit(self, ip_address: str = None, user_agent: str = None, path: str = None, user_id: int = None):
        """增加访问量"""
        try:
            # 更新今日访问统计
            stats = self.get_today_stats()
            stats.visit_count += 1
            self.db.commit()

            # 记录访问日志（可选，用于详细分析）
            if ip_address or user_agent or path:
                visit_log = VisitLog(
                    ip_address=ip_address,
                    user_agent=user_agent,
                    path=path,
                    user_id=user_id
                )
                self.db.add(visit_log)
                self.db.commit()

            logger.debug(f"[Stats] 访问量+1: {stats.stat_date}, 总计: {stats.visit_count}")
        except Exception as e:
            logger.error(f"[Stats] 更新访问量失败: {e}")
            self.db.rollback()

    def increment_register(self):
        """增加注册量"""
        try:
            stats = self.get_today_stats()
            stats.register_count += 1
            self.db.commit()
            logger.debug(f"[Stats] 注册量+1: {stats.stat_date}, 总计: {stats.register_count}")
        except Exception as e:
            logger.error(f"[Stats] 更新注册量失败: {e}")
            self.db.rollback()

    def get_stats_by_date_range(self, start_date: str, end_date: str) -> list:
        """获取指定日期范围的统计数据"""
        stats = self.db.query(SiteStats).filter(
            and_(
                SiteStats.stat_date >= start_date,
                SiteStats.stat_date <= end_date
            )
        ).order_by(SiteStats.stat_date).all()
        return [s.to_dict() for s in stats]

    def get_total_stats(self) -> dict:
        """获取总统计（累计）"""
        # 总访问量
        total_visits = self.db.query(SiteStats).with_entities(
            func.sum(SiteStats.visit_count)
        ).scalar() or 0

        # 总注册量
        total_registers = self.db.query(SiteStats).with_entities(
            func.sum(SiteStats.register_count)
        ).scalar() or 0

        # 今日统计
        today_stats = self.get_today_stats()

        return {
            "total_visits": total_visits,
            "total_registers": total_registers,
            "today_visits": today_stats.visit_count,
            "today_registers": today_stats.register_count
        }


# 导入 SQLAlchemy 的 func
from sqlalchemy import func
