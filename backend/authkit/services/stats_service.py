"""
统计服务 - 支持 Redis 缓存 + 多站点
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

    def get_today_stats(self, site: str = "zh") -> dict:
        """获取今日统计数据（优先从 Redis）"""
        today = date.today().isoformat()

        if self.redis_client:
            visit_key = f"stats:visits:{today}:{site}"
            visits = self.redis_client.get(visit_key)
            visits = int(visits) if visits else 0

            stats = self.db.query(SiteStats).filter_by(stat_date=today, site=site).first()
            registers = stats.register_count if stats else 0

            return {"stat_date": today, "site": site, "visit_count": visits, "register_count": registers}

        stats = self.db.query(SiteStats).filter_by(stat_date=today, site=site).first()
        if not stats:
            return {"stat_date": today, "site": site, "visit_count": 0, "register_count": 0}
        return stats.to_dict()

    def increment_visit(self, site: str = "zh", ip_address: str = None, user_agent: str = None, path: str = None, user_id: int = None):
        """增加访问量"""
        try:
            today = date.today().isoformat()

            if self.redis_client:
                visit_key = f"stats:visits:{today}:{site}"
                self.redis_client.incr(visit_key)
                self.redis_client.expire(visit_key, 86400 * 7)
                return

            stats = self.db.query(SiteStats).filter_by(stat_date=today, site=site).first()
            if not stats:
                stats = SiteStats(stat_date=today, site=site, visit_count=0, register_count=0)
                self.db.add(stats)
            stats.visit_count += 1
            self.db.commit()
        except Exception as e:
            logger.error(f"[Stats] 更新访问量失败: {e}")
            self.db.rollback()

    def increment_register(self, site: str = "zh"):
        """增加注册量"""
        try:
            today = date.today().isoformat()
            stats = self.db.query(SiteStats).filter_by(stat_date=today, site=site).first()
            if not stats:
                stats = SiteStats(stat_date=today, site=site, visit_count=0, register_count=0)
                self.db.add(stats)
            stats.register_count += 1
            self.db.commit()
            logger.debug(f"[Stats] 注册量+1: {today}/{site}, 总计: {stats.register_count}")
        except Exception as e:
            logger.error(f"[Stats] 更新注册量失败: {e}")
            self.db.rollback()

    def get_stats_by_date_range(self, start_date: str, end_date: str, site: Optional[str] = None) -> list:
        """获取指定日期范围的统计数据。site=None 表示汇总所有站点"""
        query = self.db.query(SiteStats).filter(
            and_(SiteStats.stat_date >= start_date, SiteStats.stat_date <= end_date)
        )
        if site:
            query = query.filter_by(site=site)

        stats = query.order_by(SiteStats.stat_date).all()

        if site:
            return [s.to_dict() for s in stats]

        # 汇总：按日期合并 zh + en
        merged = {}
        for s in stats:
            d = s.stat_date
            if d not in merged:
                merged[d] = {"stat_date": d, "visit_count": 0, "register_count": 0}
            merged[d]["visit_count"] += s.visit_count or 0
            merged[d]["register_count"] += s.register_count or 0
        return [merged[d] for d in sorted(merged.keys())]

    def get_total_stats(self, site: Optional[str] = None) -> dict:
        """获取总统计（累计）。site=None 表示汇总所有站点"""
        query_visits = self.db.query(func.sum(SiteStats.visit_count))
        query_regs = self.db.query(func.sum(SiteStats.register_count))

        if site:
            query_visits = query_visits.filter_by(site=site)
            query_regs = query_regs.filter_by(site=site)

        total_visits = query_visits.scalar() or 0
        total_registers = query_regs.scalar() or 0

        # 加上 Redis 中最近 7 天的访问量
        if self.redis_client:
            for i in range(7):
                date_str = (date.today() - timedelta(days=i)).isoformat()
                if site:
                    keys = [f"stats:visits:{date_str}:{site}"]
                else:
                    keys = [f"stats:visits:{date_str}:zh", f"stats:visits:{date_str}:en"]
                for key in keys:
                    v = self.redis_client.get(key)
                    if v:
                        total_visits += int(v)

        today_stats = self.get_today_stats(site or "zh")
        # site=None 时汇总两个站点今日数据
        if not site:
            today_stats_en = self.get_today_stats("en")
            today_stats["visit_count"] += today_stats_en.get("visit_count", 0)
            today_stats["register_count"] += today_stats_en.get("register_count", 0)

        return {
            "total_visits": total_visits,
            "total_registers": total_registers,
            "today_visits": today_stats.get("visit_count", 0),
            "today_registers": today_stats.get("register_count", 0),
        }
