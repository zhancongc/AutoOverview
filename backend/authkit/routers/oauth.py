"""
OAuth 登录适配层 — 连接 authkit.oauth 标准模块和 AutoOverview 业务逻辑
"""
import json
import logging
import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..models import User
from ..models.schemas import UserResponse
from ..core.security import create_access_token
from ..oauth import OAuthConfig, create_oauth_router

logger = logging.getLogger(__name__)

# ==================== 配置 ====================

_ALIPAY_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_oauth_config = OAuthConfig(
    alipay_app_id=os.getenv("ALIPAY_APP_ID", ""),
    alipay_private_key=os.getenv("ALIPAY_PRIVATE_KEY", ""),
    alipay_public_key=os.getenv("ALIPAY_PUBLIC_KEY", ""),
    alipay_private_key_path="app_secrets.txt",
    alipay_public_key_path="alipay_public_key.txt",
    alipay_base_dir=_ALIPAY_BASE_DIR,
    google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
    google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
    google_redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", ""),
    http_proxy=os.getenv("HTTP_PROXY", "socks5://127.0.0.1:1080") or os.getenv("http_proxy", ""),
)

_FRONTEND_URLS = {
    "zh": os.getenv("FRONTEND_URL", "").rstrip("/"),
    "en": os.getenv("EN_FRONTEND_URL", "").rstrip("/"),
}

# ==================== 业务回调 ====================

_default_get_db = None


def set_get_db(get_db_func):
    global _default_get_db
    _default_get_db = get_db_func


def set_redis_client(redis_client):
    global _redis_client
    _redis_client = redis_client


_redis_client = None


def _get_frontend_base(request: Request) -> str:
    host = request.headers.get("host") or ""
    if "en-" in host:
        return _FRONTEND_URLS["en"]
    if _FRONTEND_URLS["zh"]:
        return _FRONTEND_URLS["zh"]
    return str(request.url).split("/api/")[0]


async def _find_or_create_user(
    *, provider: str, provider_user_id: str, email: str, nickname: str, avatar_url: str,
) -> User:
    db: Session = next(_default_get_db())

    # 1. 通过 meta_data 中的 OAuth ID 查找
    for u in db.query(User).all():
        if u.get_meta(f"{provider}_user_id") == provider_user_id:
            u.last_login_at = datetime.utcnow()
            if nickname and not u.nickname:
                u.nickname = nickname
            if avatar_url and not u.avatar_url:
                u.avatar_url = avatar_url
            db.commit()
            db.refresh(u)
            return u

    # 2. 通过 email 查找（已有账号则绑定）
    if email:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            existing.set_meta(f"{provider}_user_id", provider_user_id)
            existing.last_login_at = datetime.utcnow()
            if nickname and not existing.nickname:
                existing.nickname = nickname
            if avatar_url and not existing.avatar_url:
                existing.avatar_url = avatar_url
            db.commit()
            db.refresh(existing)
            return existing

    # 3. 创建新用户
    user = User(
        email=email or f"{provider}_{provider_user_id[:16]}@oauth.danmo.tech",
        nickname=nickname or f"{provider}_user",
        avatar_url=avatar_url,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    user.set_meta("free_credits", 0)
    user.set_meta("review_credits", 2)
    user.set_meta("has_purchased", False)
    user.set_meta(f"{provider}_user_id", provider_user_id)
    db.commit()
    db.refresh(user)

    try:
        from ..services.stats_service import StatsService
        StatsService(db).increment_register()
    except Exception:
        pass

    logger.info(f"[OAuth] 新用户注册: provider={provider}, email={user.email}")
    return user


async def _make_token_response(user: User, frontend_base: str) -> RedirectResponse:
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    user_json = json.dumps(UserResponse.from_user(user).dict(), ensure_ascii=False)
    params = urlencode({"token": access_token, "user": user_json})
    return RedirectResponse(url=f"{frontend_base}/login?oauth_callback=1&{params}")


# ==================== 路由构建 ====================

def create_router(redis_client=None) -> "APIRouter":
    """供 main.py 调用，延迟创建路由（确保 redis_client 已就绪）"""
    from fastapi import APIRouter

    if redis_client is None:
        redis_client = _redis_client

    return create_oauth_router(
        config=_oauth_config,
        find_or_create_user=_find_or_create_user,
        make_token_response=_make_token_response,
        get_frontend_base=_get_frontend_base,
        redis_client=redis_client,
    )


# 兼容旧集成方式：模块级 router（Redis 在 set_redis_client 后需 rebuild）
# main.py 应改用 create_router() 代替
router = create_oauth_router(
    config=_oauth_config,
    find_or_create_user=_find_or_create_user,
    make_token_response=_make_token_response,
    get_frontend_base=_get_frontend_base,
    redis_client=None,
)
