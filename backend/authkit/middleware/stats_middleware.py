"""
访问量统计中间件 - DDoS 防护版本

使用 Redis 缓存计数，定期批量写入数据库，避免 DDoS 攻击导致数据库崩溃。
"""
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import os

logger = logging.getLogger(__name__)


class StatsMiddleware(BaseHTTPMiddleware):
    """访问量统计中间件（DDoS 防护版本）"""

    # 类变量，存储共享的 Redis 客户端
    _shared_redis_client = None

    def __init__(
        self,
        app,
        get_db_func=None,
        redis_client=None,
        exclude_paths: list = None,
        enable_visit_log: bool = False,
        rate_limit_per_minute: int = 100
    ):
        super().__init__(app)
        self.get_db_func = get_db_func
        # 优先使用传入的 redis_client，否则使用共享的
        self.redis_client = redis_client or self._shared_redis_client
        self.enable_visit_log = enable_visit_log  # 默认不记录详细日志，避免磁盘爆炸

        # 排除的路径（不统计）
        self.exclude_paths = exclude_paths or [
            "/api/health",
            "/api/stats",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        ]

        # 限流配置（每个 IP 每分钟最大请求数）
        self.rate_limit_per_minute = rate_limit_per_minute

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否需要统计
        path = request.url.path

        # 排除特定路径
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        # 排除静态资源
        if path.startswith("/static/") or path.endswith((".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico")):
            return await call_next(request)

        # 获取客户端信息
        client_ip = self._get_client_ip(request)

        # 使用共享的 Redis 客户端（类变量）
        redis_client = self.redis_client or self._shared_redis_client

        # 限流检查（防止 DDoS）
        if redis_client and not self._check_rate_limit(client_ip, redis_client):
            logger.warning(f"[StatsMiddleware] IP {client_ip} 超过限流阈值")
            # 不阻止请求，只记录警告（可选：返回 429）
            # return Response(status_code=429, content="Too Many Requests")

        # 使用 Redis 计数（不直接写数据库）
        if redis_client:
            try:
                import asyncio
                asyncio.create_task(self._record_visit_async(client_ip, path, redis_client))
            except Exception as e:
                logger.error(f"[StatsMiddleware] 异步记录访问失败: {e}")

        # 继续处理请求
        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 使用客户端地址
        if request.client:
            return request.client.host

        return "unknown"

    def _check_rate_limit(self, ip_address: str, redis_client) -> bool:
        """检查 IP 是否超过限流阈值"""
        try:
            from datetime import datetime
            key = f"rate_limit:{ip_address}:{datetime.now().strftime('%Y%m%d%H%M')}"

            current = redis_client.get(key)
            if current is None:
                redis_client.setex(key, 60, 1)
                return True

            current = int(current)
            if current >= self.rate_limit_per_minute:
                return False

            redis_client.incr(key)
            return True
        except Exception as e:
            logger.error(f"[StatsMiddleware] 限流检查失败: {e}")
            return True  # 出错时不限流

    async def _record_visit_async(self, ip_address: str, path: str, redis_client):
        """异步记录访问（使用 Redis，不直接写数据库）"""
        try:
            from datetime import date

            today = date.today().isoformat()

            # 使用 Redis 计数器
            visit_key = f"stats:visits:{today}"
            redis_client.incr(visit_key)
            redis_client.expire(visit_key, 86400 * 7)  # 保留 7 天

            # 如果启用详细日志，采样记录（10% 概率，避免数据爆炸）
            if self.enable_visit_log and hash(ip_address + path) % 10 == 0:
                log_key = f"stats:logs:{today}"
                log_data = f"{ip_address}:{path}"
                redis_client.rpush(log_key, log_data)
                redis_client.expire(log_key, 86400 * 7)  # 保留 7 天

        except Exception as e:
            logger.error(f"[StatsMiddleware] Redis 记录失败: {e}")


class StatsBatchWriter:
    """
    批量写入器：定期将 Redis 中的统计数据同步到数据库

    使用方式：
    在应用启动时启动后台任务：
        writer = StatsBatchWriter(redis_client=redis, get_db_func=auth_get_db)
        asyncio.create_task(writer.start())
    """

    def __init__(self, redis_client, get_db_func, interval_seconds: int = 300):
        """
        Args:
            redis_client: Redis 客户端
            get_db_func: 数据库会话获取函数
            interval_seconds: 同步间隔（秒），默认 5 分钟
        """
        self.redis_client = redis_client
        self.get_db_func = get_db_func
        self.interval_seconds = interval_seconds

    async def start(self):
        """启动后台同步任务"""
        import asyncio
        from datetime import date

        logger.info("[StatsBatchWriter] 启动统计批量写入任务")

        while True:
            try:
                await asyncio.sleep(self.interval_seconds)
                await self._sync_to_db()
            except Exception as e:
                logger.error(f"[StatsBatchWriter] 同步失败: {e}")

    async def _sync_to_db(self):
        """将 Redis 数据同步到数据库"""
        try:
            from datetime import date, timedelta

            # 同步最近 7 天的数据
            today = date.today()
            db_gen = self.get_db_func()
            db = next(db_gen)

            try:
                from ..services.stats_service import StatsService
                stats_service = StatsService(db)

                for i in range(7):
                    stat_date = (today - timedelta(days=i)).isoformat()
                    visit_key = f"stats:visits:{stat_date}"

                    # 从 Redis 获取访问量
                    visits = self.redis_client.get(visit_key)
                    if visits:
                        visits = int(visits)

                        # 检查数据库中是否已有该日期的记录
                        from ..models.stats import SiteStats
                        existing = db.query(SiteStats).filter_by(stat_date=stat_date).first()

                        if existing:
                            # 更新现有记录
                            existing.visit_count = visits
                        else:
                            # 创建新记录
                            new_stat = SiteStats(stat_date=stat_date, visit_count=visits, register_count=0)
                            db.add(new_stat)

                        db.commit()
                        logger.debug(f"[StatsBatchWriter] 同步 {stat_date}: {visits} 次访问")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"[StatsBatchWriter] 同步到数据库失败: {e}")
