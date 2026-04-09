"""
认证服务 - 核心业务逻辑
"""
import logging
from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from ..models import User
from ..models.schemas import UserCreate, UserResponse
from ..core.security import (
    hash_password,
    verify_password,
    validate_password,
    generate_verification_code,
    create_access_token
)
from ..core.validator import is_valid_email, sanitize_email
from ..services.email_service import email_service
from ..services.cache_service import cache_service
from ..core.config import config


class AuthService:
    """认证服务"""

    def __init__(self, db: Session):
        self.db = db

    def register_by_password(self, user_data: UserCreate) -> Tuple[bool, str, Optional[UserResponse]]:
        """
        密码注册

        Returns:
            (success, message, user)
        """
        # 验证邮箱
        if not is_valid_email(user_data.email):
            return False, "邮箱格式不正确", None

        email = sanitize_email(user_data.email)

        # 验证密码
        is_valid, error_msg = validate_password(user_data.password)
        if not is_valid:
            return False, error_msg, None

        # 检查邮箱是否已存在
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            return False, "该邮箱已被注册", None

        # 创建用户
        hashed_password = hash_password(user_data.password)
        new_user = User(
            email=email,
            hashed_password=hashed_password,
            nickname=user_data.nickname or email.split('@')[0],
            gender=user_data.gender if hasattr(user_data, 'gender') else 0,
            country=getattr(user_data, 'country', None),
            province=getattr(user_data, 'province', None),
            city=getattr(user_data, 'city', None),
            is_active=True,
            is_verified=False
        )

        # 设置扩展元数据（如果有）
        if hasattr(user_data, 'metadata') and user_data.metadata:
            new_user.set_metadata(user_data.metadata)

        try:
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)

            # 注册送 1 篇免费综述额度（可生成，不可导出 Word）
            new_user.set_meta("free_credits", 1)
            new_user.set_meta("review_credits", 0)
            new_user.set_meta("has_purchased", False)
            self.db.commit()

            # 发送欢迎邮件
            email_service.send_welcome_email(email, new_user.nickname)

            return True, "注册成功", UserResponse.from_user(new_user)

        except Exception as e:
            self.db.rollback()
            logger.error("注册失败: email=%s, error=%s", email, e, exc_info=True)
            return False, f"注册失败: {str(e)}", None

    def login_by_password(self, email: str, password: str) -> Tuple[bool, str, Optional[dict]]:
        """
        密码登录

        Returns:
            (success, message, data)
            data 包含: access_token, user
        """
        # 验证邮箱
        if not is_valid_email(email):
            return False, "邮箱格式不正确", None

        email = sanitize_email(email)

        # 查找用户
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return False, "邮箱或密码错误", None

        # 验证密码
        if not user.hashed_password:
            return False, "该账号未设置密码，请使用验证码登录", None

        if not verify_password(password, user.hashed_password):
            return False, "邮箱或密码错误", None

        # 检查账号状态
        if not user.is_active:
            return False, "账号已被禁用", None

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        self.db.commit()

        # 生成 Token
        access_token = create_access_token({"sub": str(user.id), "email": user.email})

        return True, "登录成功", {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.from_user(user)
        }

    def send_verification_code(self, email: str, purpose: str = "login") -> Tuple[bool, str]:
        """
        发送验证码

        Args:
            email: 邮箱
            purpose: 用途 (login/register/reset_password)

        Returns:
            (success, message)
        """
        # 验证邮箱
        if not is_valid_email(email):
            return False, "邮箱格式不正确"

        email = sanitize_email(email)

        # 检查是否频繁发送
        if cache_service.check_code_sent_recently(email, purpose):
            return False, "验证码已发送，请60秒后再试"

        # 对于注册，检查邮箱是否已存在
        if purpose == "register":
            existing_user = self.db.query(User).filter(User.email == email).first()
            if existing_user:
                return False, "该邮箱已被注册"

        # 对于重置密码，检查邮箱是否存在
        if purpose == "reset_password":
            existing_user = self.db.query(User).filter(User.email == email).first()
            if not existing_user:
                return False, "该邮箱未注册"

        # 登录时不再检查邮箱是否存在，支持自动注册

        # 生成验证码
        code = generate_verification_code()

        # 保存到缓存
        if not cache_service.save_verification_code(email, code, purpose):
            return False, "验证码保存失败，请稍后重试"

        # 发送邮件
        if not email_service.send_verification_code(email, code, purpose):
            return False, "邮件发送失败，请稍后重试"

        # 标记已发送
        cache_service.mark_code_sent(email, purpose)

        return True, "验证码已发送到您的邮箱"

    def login_by_code(self, email: str, code: str) -> Tuple[bool, str, Optional[dict]]:
        """
        验证码登录

        Returns:
            (success, message, data)
        """
        # 验证邮箱
        if not is_valid_email(email):
            return False, "邮箱格式不正确", None

        email = sanitize_email(email)

        # 验证验证码
        if not cache_service.verify_code(email, code, "login"):
            return False, "验证码错误或已过期", None

        # 查找或创建用户
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # 自动注册
            user = User(
                email=email,
                nickname=email.split('@')[0],
                is_active=True,
                is_verified=True
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            # 注册送 1 篇免费综述额度（可生成，不可导出 Word）
            user.set_meta("free_credits", 1)
            user.set_meta("review_credits", 0)
            user.set_meta("has_purchased", False)
            self.db.commit()
        else:
            # 更新最后登录时间
            user.last_login_at = datetime.utcnow()
            user.is_verified = True
            self.db.commit()

        # 生成 Token
        access_token = create_access_token({"sub": str(user.id), "email": user.email})

        return True, "登录成功", {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.from_user(user)
        }

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()

    def update_user(
        self,
        user_id: int,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None,
        gender: Optional[int] = None,
        country: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        language: Optional[str] = None
    ) -> Tuple[bool, str, Optional[UserResponse]]:
        """更新用户信息"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "用户不存在", None

        if nickname is not None:
            user.nickname = nickname
        if avatar_url is not None:
            user.avatar_url = avatar_url
        if gender is not None:
            user.gender = gender
        if country is not None:
            user.country = country
        if province is not None:
            user.province = province
        if city is not None:
            user.city = city
        if language is not None:
            user.language = language

        try:
            self.db.commit()
            self.db.refresh(user)
            return True, "更新成功", UserResponse.from_user(user)
        except Exception as e:
            self.db.rollback()
            logger.error("更新用户信息失败: error=%s", e, exc_info=True)
            return False, f"更新失败: {str(e)}", None

    def reset_password(self, email: str, code: str, new_password: str) -> Tuple[bool, str]:
        """重置密码"""
        # 验证邮箱
        if not is_valid_email(email):
            return False, "邮箱格式不正确"

        email = sanitize_email(email)

        # 验证验证码
        if not cache_service.verify_code(email, code, "reset_password"):
            return False, "验证码错误或已过期"

        # 验证密码
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            return False, error_msg

        # 更新密码
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return False, "用户不存在"

        user.hashed_password = hash_password(new_password)

        try:
            self.db.commit()
            return True, "密码重置成功"
        except Exception as e:
            self.db.rollback()
            logger.error("密码重置失败: email=%s, error=%s", email, e, exc_info=True)
            return False, f"重置失败: {str(e)}"
