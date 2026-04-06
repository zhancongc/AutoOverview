"""
Pydantic 模型（通用版本，可复用）
"""
from pydantic import BaseModel, EmailStr, Field, field_serializer
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    nickname: Optional[str] = None


class UserCreate(UserBase):
    """创建用户请求"""
    password: str
    nickname: Optional[str] = None
    gender: Optional[int] = 0
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    metadata: Optional[dict] = None  # 扩展元数据


class UserLogin(BaseModel):
    """用户登录请求"""
    email: EmailStr
    password: str


class UserLoginWithCode(BaseModel):
    """验证码登录请求"""
    email: EmailStr
    code: str


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    email: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: int = 0
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    language: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_staff: bool
    metadata: Optional[dict] = None  # 扩展元数据
    created_at: Optional[str] = None

    @field_serializer('created_at')
    def serialize_created_at(self, created_at: Optional[datetime | str]) -> Optional[str]:
        """将 datetime 转换为 ISO 格式字符串"""
        if created_at:
            if isinstance(created_at, datetime):
                return created_at.isoformat()
            return created_at
        return None

    class Config:
        from_attributes = True

    @classmethod
    def from_user(cls, user):
        """从 User 模型创建响应"""
        return cls(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            gender=user.gender or 0,
            country=user.country,
            province=user.province,
            city=user.city,
            language=user.language,
            is_active=user.is_active if user.is_active is not None else True,
            is_verified=user.is_verified if user.is_verified is not None else False,
            is_staff=user.is_staff if user.is_staff is not None else False,
            metadata=user.get_metadata(),
            created_at=user.created_at.isoformat() if user.created_at else None
        )


class UserUpdate(BaseModel):
    """更新用户信息"""
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    language: Optional[str] = None
    metadata: Optional[dict] = None  # 更新元数据


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    email: EmailStr
    purpose: str = Field(..., description="用途: register/login/reset_password")


class APIResponse(BaseModel):
    """通用 API 响应"""
    success: bool
    message: str
    data: Optional[dict] = None
