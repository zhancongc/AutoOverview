"""
Redis 客户端管理 — 单例连接池
"""
import logging
from typing import Optional

from .config import RedisConfig

logger = logging.getLogger(__name__)

_shared_client = None


def init_redis(config: RedisConfig = None) -> Optional['redis.Redis']:
    """初始化共享 Redis 客户端（单例）。返回客户端实例，失败返回 None。"""
    global _shared_client

    if _shared_client is not None:
        return _shared_client

    import redis as _redis

    cfg = config or RedisConfig()

    try:
        _shared_client = _redis.Redis(
            host=cfg.host,
            port=cfg.port,
            db=cfg.db,
            password=cfg.password,
            decode_responses=cfg.decode_responses,
            socket_timeout=cfg.socket_timeout,
            socket_connect_timeout=cfg.socket_connect_timeout,
            max_connections=cfg.max_connections,
        )
        _shared_client.ping()
        logger.info(f"[Redis] 连接成功 {cfg.host}:{cfg.port}/{cfg.db}")
    except Exception as e:
        logger.warning(f"[Redis] 连接失败: {e}")
        _shared_client = None

    return _shared_client


def get_redis() -> Optional['redis.Redis']:
    """获取共享 Redis 客户端。如未初始化会自动尝试初始化。"""
    global _shared_client
    if _shared_client is None:
        _shared_client = init_redis()
    return _shared_client
