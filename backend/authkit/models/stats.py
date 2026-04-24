"""
网站统计数据模型
"""
from sqlalchemy import Column, Integer, BigInteger, DateTime, String, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

StatsBase = declarative_base()


class SiteStats(StatsBase):
    """网站统计表"""
    __tablename__ = "site_stats"
    __table_args__ = (
        UniqueConstraint("stat_date", "site", name="uq_site_stats_date_site"),
    )

    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(String(10), nullable=False, comment="统计日期 (YYYY-MM-DD)")
    site = Column(String(10), default="zh", nullable=False, comment="站点: zh/en")
    visit_count = Column(BigInteger, default=0, comment="访问量")
    register_count = Column(Integer, default=0, comment="注册用户数")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "stat_date": self.stat_date,
            "site": self.site,
            "visit_count": self.visit_count,
            "register_count": self.register_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class VisitLog(StatsBase):
    """访问日志表（用于详细记录）"""
    __tablename__ = "visit_logs"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="用户代理")
    path = Column(String(200), comment="访问路径")
    user_id = Column(Integer, comment="用户ID（如果已登录）")
    site = Column(String(10), default="zh", comment="站点: zh/en")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="访问时间")

    def to_dict(self):
        return {
            "id": self.id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "path": self.path,
            "user_id": self.user_id,
            "site": self.site,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
