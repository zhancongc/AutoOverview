"""
authkit.redis — Redis 统一管理

用法:
    from authkit.redis import init_redis, get_redis

    # 初始化（在应用启动时调用一次）
    redis_client = init_redis()

    # 获取共享客户端（任意位置）
    redis_client = get_redis()
"""
from .config import RedisConfig
from .client import init_redis, get_redis
from .patterns import RedisCache, RedisRateLimiter

__all__ = [
    "RedisConfig",
    "init_redis",
    "get_redis",
    "RedisCache",
    "RedisRateLimiter",
]
