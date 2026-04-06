"""
输入验证工具
"""
import re
from typing import Optional


def is_valid_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_email(email: str) -> str:
    """清理邮箱地址（去除空格、转小写）"""
    return email.strip().lower()


def mask_email(email: str) -> str:
    """隐藏邮箱中间部分，用于显示"""
    if '@' not in email:
        return email

    username, domain = email.split('@', 1)
    if len(username) <= 2:
        masked_username = '*' * len(username)
    else:
        masked_username = username[0] + '*' * (len(username) - 2) + username[-1]

    return f"{masked_username}@{domain}"


def is_valid_phone(phone: str) -> bool:
    """验证手机号格式（中国大陆）"""
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))
