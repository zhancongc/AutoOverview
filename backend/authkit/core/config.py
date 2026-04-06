"""
认证模块配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class AuthConfig(BaseSettings):
    """认证配置"""

    # JWT 配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # 邮件配置
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Auth Kit"

    # 验证码配置
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 10  # 验证码过期时间（分钟）
    VERIFICATION_CODE_LENGTH: int = 6  # 验证码长度

    # 密码配置
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False

    # Redis 配置（用于存储验证码）
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    class Config:
        env_prefix = "AUTH_"
        case_sensitive = True


# 全局配置实例
config = AuthConfig()
