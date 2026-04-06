"""
安全工具：JWT、密码加密等
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from .config import config

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def validate_password(password: str) -> tuple[bool, str]:
    """
    验证密码强度
    返回: (是否有效, 错误信息)
    """
    if len(password) < config.PASSWORD_MIN_LENGTH:
        return False, f"密码长度至少需要{config.PASSWORD_MIN_LENGTH}位"

    if config.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False, "密码必须包含至少一个大写字母"

    if config.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return False, "密码必须包含至少一个小写字母"

    if config.PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        return False, "密码必须包含至少一个数字"

    if config.PASSWORD_REQUIRE_SPECIAL:
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "密码必须包含至少一个特殊字符"

    return True, ""


def generate_verification_code() -> str:
    """生成验证码"""
    import random
    import string
    return ''.join(random.choices(string.digits, k=config.VERIFICATION_CODE_LENGTH))
