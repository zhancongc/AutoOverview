"""
Redis 通用工具：缓存、限流
"""
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class RedisCache:
    """带 TTL 的缓存"""

    def __init__(self, redis_client, prefix: str = "cache", default_ttl: int = 3600):
        self._redis = redis_client
        self._prefix = prefix
        self._default_ttl = default_ttl

    def _key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def get(self, key: str) -> Optional[str]:
        try:
            return self._redis.get(self._key(key))
        except Exception as e:
            logger.error(f"RedisCache get error: {e}")
            return None

    def set(self, key: str, value: str, ttl: int = None) -> bool:
        try:
            self._redis.setex(self._key(key), ttl or self._default_ttl, value)
            return True
        except Exception as e:
            logger.error(f"RedisCache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        try:
            self._redis.delete(self._key(key))
            return True
        except Exception as e:
            logger.error(f"RedisCache delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        try:
            return self._redis.exists(self._key(key)) > 0
        except Exception as e:
            logger.error(f"RedisCache exists error: {e}")
            return False


class RedisRateLimiter:
    """滑动窗口限流器"""

    def __init__(self, redis_client, prefix: str = "rate_limit"):
        self._redis = redis_client
        self._prefix = prefix

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        检查是否允许请求。
        返回 (allowed, remaining)。
        """
        try:
            from datetime import datetime
            bucket_key = f"{self._prefix}:{key}:{datetime.now().strftime('%Y%m%d%H%M')}"

            current = self._redis.get(bucket_key)
            if current is None:
                self._redis.setex(bucket_key, window_seconds, 1)
                return True, max_requests - 1

            current = int(current)
            if current >= max_requests:
                return False, 0

            self._redis.incr(bucket_key)
            return True, max_requests - current - 1
        except Exception as e:
            logger.error(f"RedisRateLimiter error: {e}")
            return True, max_requests  # 出错时放行
