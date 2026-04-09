"""
缓存服务 - 用于存储验证码
"""
import logging
import redis
from typing import Optional
import json

from ..core.config import config

logger = logging.getLogger(__name__)


class CacheService:
    """缓存服务（基于 Redis）"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_PASSWORD,
            decode_responses=True
        )

    def set(self, key: str, value: str, expire_seconds: int) -> bool:
        """设置缓存"""
        try:
            self.redis_client.setex(key, expire_seconds, value)
            return True
        except Exception as e:
            logger.error("Redis set error: key=%s, error=%s", key, e)
            return False

    def get(self, key: str) -> Optional[str]:
        """获取缓存"""
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error("Redis get error: key=%s, error=%s", key, e)
            return None

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error("Redis delete error: key=%s, error=%s", key, e)
            return False

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error("Redis exists error: key=%s, error=%s", key, e)
            return False

    # 验证码相关方法
    def save_verification_code(self, email: str, code: str, purpose: str = "login") -> bool:
        """保存验证码"""
        key = f"verification_code:{purpose}:{email}"
        expire_seconds = config.VERIFICATION_CODE_EXPIRE_MINUTES * 60
        return self.set(key, code, expire_seconds)

    def get_verification_code(self, email: str, purpose: str = "login") -> Optional[str]:
        """获取验证码"""
        key = f"verification_code:{purpose}:{email}"
        return self.get(key)

    def verify_code(self, email: str, code: str, purpose: str = "login") -> bool:
        """验证验证码"""
        stored_code = self.get_verification_code(email, purpose)
        if stored_code and stored_code == code:
            # 验证成功后删除验证码
            self.delete(f"verification_code:{purpose}:{email}")
            return True
        return False

    def check_code_sent_recently(self, email: str, purpose: str = "login") -> bool:
        """检查是否最近发送过验证码（防刷）"""
        key = f"verification_code_sent:{purpose}:{email}"
        return self.exists(key)

    def mark_code_sent(self, email: str, purpose: str = "login") -> bool:
        """标记已发送验证码（60秒内不能重复发送）"""
        key = f"verification_code_sent:{purpose}:{email}"
        return self.set(key, "1", 60)


# 全局缓存服务实例
cache_service = CacheService()
