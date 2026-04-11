"""
访问量统计中间件
"""
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable

logger = logging.getLogger(__name__)


class StatsMiddleware(BaseHTTPMiddleware):
    """访问量统计中间件"""

    def __init__(self, app, get_db_func=None, exclude_paths: list = None):
        super().__init__(app)
        self.get_db_func = get_db_func
        # 排除的路径（不统计）
        self.exclude_paths = exclude_paths or [
            "/api/health",
            "/api/stats",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        ]

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
        user_agent = request.headers.get("user-agent", "")
        user_id = None

        # 尝试获取用户ID（从JWT token）
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from ..core.security import decode_access_token
                token = auth_header.split(" ")[1]
                payload = decode_access_token(token)
                if payload:
                    user_id = int(payload.get("sub")) if payload.get("sub") else None
            except Exception:
                pass

        # 异步记录访问量（不阻塞请求）
        try:
            if self.get_db_func:
                import asyncio
                asyncio.create_task(self._record_visit(client_ip, user_agent, path, user_id))
        except Exception as e:
            logger.error(f"[StatsMiddleware] 记录访问量失败: {e}")

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

    async def _record_visit(self, ip_address: str, user_agent: str, path: str, user_id: int = None):
        """异步记录访问量"""
        try:
            if not self.get_db_func:
                return

            from ..services.stats_service import StatsService

            # 获取数据库会话
            db_gen = self.get_db_func()
            db = next(db_gen)

            try:
                stats_service = StatsService(db)
                stats_service.increment_visit(
                    ip_address=ip_address,
                    user_agent=user_agent,
                    path=path,
                    user_id=user_id
                )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[StatsMiddleware] 异步记录访问失败: {e}")
