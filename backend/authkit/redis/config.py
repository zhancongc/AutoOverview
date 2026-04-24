"""
Redis 配置
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RedisConfig:
    host: str = ""
    port: int = 6379
    db: int = 0
    password: str | None = None
    decode_responses: bool = True
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    max_connections: int = 20

    def __post_init__(self):
        # 默认从环境变量读取
        if not self.host:
            object.__setattr__(self, 'host', os.getenv("AUTH_REDIS_HOST", "localhost"))
        if self.port == 6379 and not os.getenv("AUTH_REDIS_PORT"):
            pass  # keep default
        elif os.getenv("AUTH_REDIS_PORT"):
            object.__setattr__(self, 'port', int(os.getenv("AUTH_REDIS_PORT", "6379")))
        if self.db == 0 and os.getenv("AUTH_REDIS_DB"):
            object.__setattr__(self, 'db', int(os.getenv("AUTH_REDIS_DB", "0")))
        if self.password is None and os.getenv("AUTH_REDIS_PASSWORD"):
            object.__setattr__(self, 'password', os.getenv("AUTH_REDIS_PASSWORD"))
