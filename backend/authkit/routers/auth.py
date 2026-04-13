"""
认证 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..models import Base
from ..models.schemas import (
    UserCreate,
    UserLogin,
    UserLoginWithCode,
    UserResponse,
    UserUpdate,
    TokenResponse,
    SendCodeRequest,
    APIResponse
)
from ..services import AuthService
from ..core.security import decode_access_token
from ..core.validator import mask_email

router = APIRouter(prefix="/api/auth", tags=["认证"])

# HTTP Bearer 认证
security = HTTPBearer()


# 数据库依赖（需要在主应用中提供）
_default_get_db = None

def get_db():
    """获取数据库会话（需要在主应用中实现）"""
    global _default_get_db
    if _default_get_db is not None:
        yield from _default_get_db()
        return
    raise NotImplementedError("请在主应用中实现 set_get_db() 函数")

def set_get_db(get_db_func):
    """设置数据库依赖（由主应用调用）"""
    global _default_get_db
    _default_get_db = get_db_func


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """获取认证服务"""
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserResponse:
    """获取当前登录用户"""
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(int(user_id))

    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="账号已被禁用")

    return UserResponse.from_user(user)


@router.post("/register", response_model=APIResponse)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    密码注册

    - **email**: 邮箱地址
    - **password**: 密码（至少8位，包含大小写字母和数字）
    - **nickname**: 昵称（可选）
    """
    success, message, user = auth_service.register_by_password(user_data)

    if success:
        return APIResponse(success=True, message=message, data={"user": user.model_dump()})
    else:
        return APIResponse(success=False, message=message)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    密码登录

    - **email**: 邮箱地址
    - **password**: 密码
    """
    success, message, data = auth_service.login_by_password(login_data.email, login_data.password)

    if success:
        return data
    else:
        raise HTTPException(status_code=400, detail=message)


@router.post("/send-code", response_model=APIResponse)
async def send_code(
    request: SendCodeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    发送验证码

    - **email**: 邮箱地址
    - **purpose**: 用途 (login/register/reset_password)
    """
    success, message = auth_service.send_verification_code(request.email, request.purpose, request.language)

    if success:
        # 隐藏邮箱中间部分
        masked_email = mask_email(request.email)
        return APIResponse(
            success=True,
            message=f"验证码已发送到 {masked_email}"
        )
    else:
        return APIResponse(success=False, message=message)


@router.post("/login-with-code", response_model=TokenResponse)
async def login_with_code(
    login_data: UserLoginWithCode,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    验证码登录

    - **email**: 邮箱地址
    - **code**: 6位验证码
    """
    success, message, data = auth_service.login_by_code(login_data.email, login_data.code)

    if success:
        return data
    else:
        raise HTTPException(status_code=400, detail=message)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user


@router.put("/me", response_model=APIResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息（支持昵称、头像、地区等信息）"""
    auth_service = AuthService(db)
    success, message, user = auth_service.update_user(
        current_user.id,
        nickname=update_data.nickname,
        avatar_url=update_data.avatar_url,
        gender=update_data.gender,
        country=update_data.country,
        province=update_data.province,
        city=update_data.city,
        language=update_data.language
    )

    if success:
        return APIResponse(success=True, message=message, data={"user": user.model_dump()})
    else:
        return APIResponse(success=False, message=message)


@router.post("/reset-password", response_model=APIResponse)
async def reset_password(
    email: str,
    code: str,
    new_password: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    重置密码

    - **email**: 邮箱地址
    - **code**: 验证码
    - **new_password**: 新密码
    """
    success, message = auth_service.reset_password(email, code, new_password)

    if success:
        return APIResponse(success=True, message=message)
    else:
        return APIResponse(success=False, message=message)


@router.get("/me/stats")
async def get_user_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户统计信息（基础版本）

    返回：
    - 用户基本信息
    - 元数据（可用于扩展业务统计）
    """
    # 从 metadata 中获取业务统计数据
    from ..models import User
    user = db.query(User).filter(User.id == current_user.id).first()

    if user:
        meta_data = user.get_metadata()
        return {
            "success": True,
            "data": {
                "user_id": current_user.id,
                "email": current_user.email,
                "nickname": current_user.nickname,
                "is_verified": current_user.is_verified,
                "created_at": current_user.created_at,
                # metadata 用于存储业务特定数据
                "metadata": meta_data
            }
        }
    else:
        return {
            "success": False,
            "message": "用户不存在"
        }
