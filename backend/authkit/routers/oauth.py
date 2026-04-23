"""
OAuth 第三方登录路由（支付宝 + Google）
"""
import os
import secrets
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..models import User
from ..models.schemas import UserResponse
from ..core.security import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["OAuth 登录"])

_default_get_db = None

# Nginx 反向代理下 request.url 是内部地址，用环境变量指定前端地址
_FRONTEND_URLS = {
    "zh": os.getenv("FRONTEND_URL", "").rstrip("/"),
    "en": os.getenv("EN_FRONTEND_URL", "").rstrip("/"),
}


def _get_frontend_base(request: Request) -> str:
    """根据请求来源判断前端地址"""
    # 从 Host 头判断中英文站
    host = request.headers.get("host") or ""
    if "en-" in host:
        return _FRONTEND_URLS["en"]
    if _FRONTEND_URLS["zh"]:
        return _FRONTEND_URLS["zh"]
    return str(request.url).split("/api/")[0]


def get_db():
    global _default_get_db
    if _default_get_db is not None:
        yield from _default_get_db()
        return
    raise NotImplementedError("OAuth router: 请先调用 set_get_db()")


def set_get_db(get_db_func):
    global _default_get_db
    _default_get_db = get_db_func


# ==================== State 管理 ====================
# 多 worker 下必须用 Redis 存储 state，否则跨 worker 验证失败
_state_store: dict = {}  # Redis 不可用时的内存兜底
_redis_client = None


def set_redis_client(redis_client):
    global _redis_client
    _redis_client = redis_client


def _generate_state(provider: str) -> str:
    state = secrets.token_urlsafe(32)
    data = json.dumps({"provider": provider, "created_at": datetime.utcnow().timestamp()})
    if _redis_client:
        _redis_client.setex(f"oauth:state:{state}", 600, data)
    else:
        _state_store[state] = {"provider": provider, "created_at": datetime.utcnow().timestamp()}
    return state


def _verify_state(state: str) -> Optional[str]:
    if _redis_client:
        raw = _redis_client.getdel(f"oauth:state:{state}")
        if not raw:
            return None
        entry = json.loads(raw)
        return entry["provider"]
    # 内存兜底
    entry = _state_store.pop(state, None)
    if not entry:
        return None
    elapsed = datetime.utcnow().timestamp() - entry["created_at"]
    if elapsed > 600:
        return None
    return entry["provider"]


# ==================== 用户创建/查找 ====================

def _find_or_create_oauth_user(
    db: Session,
    provider: str,
    provider_user_id: str,
    email: str,
    nickname: str = "",
    avatar_url: str = "",
) -> User:
    """查找已有 OAuth 用户，或创建新用户"""
    # 1. 通过 meta_data 中的 OAuth ID 查找
    users = db.query(User).all()
    for u in users:
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

    # 注册送 2 积分
    user.set_meta("free_credits", 0)
    user.set_meta("review_credits", 2)
    user.set_meta("has_purchased", False)
    user.set_meta(f"{provider}_user_id", provider_user_id)
    db.commit()
    db.refresh(user)

    # 注册统计
    try:
        from ..services.stats_service import StatsService
        StatsService(db).increment_register()
    except Exception:
        pass

    logger.info(f"[OAuth] 新用户注册: provider={provider}, email={user.email}")
    return user


def _make_token_response(user: User, frontend_base: str) -> RedirectResponse:
    """生成 JWT 并重定向到前端"""
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    user_json = json.dumps(UserResponse.from_user(user).dict(), ensure_ascii=False)

    params = urlencode({
        "token": access_token,
        "user": user_json,
    })
    return RedirectResponse(url=f"{frontend_base}/login?oauth_callback=1&{params}")


# ==================== 支付宝登录 ====================

ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "")
ALIPAY_GATEWAY = "https://openapi.alipay.com/gateway.do"


def _load_alipay_key(env_val: str, default_path: str) -> str:
    """加载支付宝密钥：优先用 env 变量值，否则从文件读取"""
    if env_val:
        return env_val
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    full_path = os.path.join(base_dir, default_path)
    if os.path.exists(full_path):
        with open(full_path, "r") as f:
            return f.read().strip()
    return ""


ALIPAY_PRIVATE_KEY = _load_alipay_key(os.getenv("ALIPAY_PRIVATE_KEY", ""), "app_secrets.txt")
ALIPAY_PUBLIC_KEY = _load_alipay_key(os.getenv("ALIPAY_PUBLIC_KEY", ""), "alipay_public_key.txt")


@router.get("/alipay/authorize")
async def alipay_authorize(request: Request):
    """生成支付宝授权链接，前端跳转到此 URL"""
    if not ALIPAY_APP_ID:
        raise HTTPException(status_code=500, detail="支付宝登录未配置")

    frontend_base = _get_frontend_base(request)
    redirect_uri = f"{frontend_base}/api/auth/alipay/callback"
    state = _generate_state("alipay")

    params = {
        "app_id": ALIPAY_APP_ID,
        "redirect_uri": redirect_uri,
        "scope": "auth_user",
        "state": state,
        "response_type": "code",
    }
    auth_url = f"https://openauth.alipay.com/oauth2/publicAppAuthorize.htm?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/alipay/callback")
async def alipay_callback(
    auth_code: Optional[str] = None,
    code: Optional[str] = None,
    state: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """支付宝授权回调"""
    frontend_base = _get_frontend_base(request)

    # 支付宝用 auth_code，兜底 code
    code = auth_code or code
    if not code or not state:
        return RedirectResponse(url=f"{frontend_base}/login?oauth_error=denied")

    provider = _verify_state(state)
    if provider != "alipay":
        return RedirectResponse(url=f"{frontend_base}/login?oauth_error=invalid_state")

    try:
        # 用 auth_code 换 access_token
        token_data = _alipay_get_token(code)
        if not token_data:
            return RedirectResponse(url=f"{frontend_base}/login?oauth_error=token_failed")

        access_token = token_data.get("access_token")
        user_id = token_data.get("user_id")

        # 获取用户信息
        user_info = _alipay_get_user_info(access_token)
        nickname = user_info.get("nick_name", "")
        avatar = user_info.get("avatar", "")

        # 查找/创建用户
        user = _find_or_create_oauth_user(
            db=db, provider="alipay", provider_user_id=user_id,
            email="", nickname=nickname, avatar_url=avatar,
        )
        return _make_token_response(user, frontend_base)

    except Exception as e:
        logger.error(f"[OAuth] Alipay callback error: {e}", exc_info=True)
        return RedirectResponse(url=f"{frontend_base}/login?oauth_error=server_error")


def _alipay_get_token(auth_code: str) -> dict:
    """用 auth_code 换 access_token"""
    try:
        import httpx
        from alipay import AliPay

        alipay = AliPay(
            appid=ALIPAY_APP_ID,
            app_private_key_string=ALIPAY_PRIVATE_KEY,
            alipay_public_key_string=ALIPAY_PUBLIC_KEY,
            sign_type="RSA2",
        )
        result, error = alipay.get_oauth_token(auth_code)
        if error:
            logger.error(f"[Alipay] get_token error: {error}")
            return {}
        return result
    except ImportError:
        # fallback: 手动请求
        return _alipay_get_token_manual(auth_code)
    except Exception as e:
        logger.error(f"[Alipay] get_token exception: {e}")
        return {}


def _alipay_get_token_manual(auth_code: str) -> dict:
    """手动换取 token（无 SDK 兜底）"""
    import httpx
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    import base64

    params = {
        "app_id": ALIPAY_APP_ID,
        "method": "alipay.system.oauth.token",
        "charset": "utf-8",
        "sign_type": "RSA2",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0",
        "grant_type": "authorization_code",
        "code": auth_code,
    }
    # 注意: 实际生产环境需要正确签名, 建议安装 python-alipay-sdk
    logger.warning("[Alipay] 使用手动模式，建议安装 python-alipay-sdk")
    return {}


def _alipay_get_user_info(access_token: str) -> dict:
    """获取支付宝用户信息"""
    try:
        from alipay import AliPay

        alipay = AliPay(
            appid=ALIPAY_APP_ID,
            app_private_key_string=ALIPAY_PRIVATE_KEY,
            alipay_public_key_string=ALIPAY_PUBLIC_KEY,
            sign_type="RSA2",
        )
        result = alipay.api_alipay_user_info_share(auth_token=access_token)
        if result.get("code") == "10000":
            return {
                "user_id": result.get("user_id", ""),
                "nick_name": result.get("nick_name", ""),
                "avatar": result.get("avatar", ""),
            }
        logger.error(f"[Alipay] user_info error: {result}")
        return {}
    except Exception as e:
        logger.error(f"[Alipay] user_info exception: {e}")
        return {}


# ==================== Google 登录 ====================

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# 国内服务器访问 Google API 需要代理
HTTP_PROXY = os.getenv("HTTP_PROXY", "") or os.getenv("http_proxy", "")


def _get_httpx_client():
    kwargs = {"timeout": 15.0}
    if HTTP_PROXY:
        kwargs["proxy"] = HTTP_PROXY
    return httpx.AsyncClient(**kwargs)


@router.get("/google/authorize")
async def google_authorize(request: Request):
    """生成 Google 授权链接"""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google 登录未配置")

    if GOOGLE_REDIRECT_URI:
        redirect_uri = GOOGLE_REDIRECT_URI
    else:
        frontend_base = _get_frontend_base(request)
        redirect_uri = f"{frontend_base}/api/auth/google/callback"
    state = _generate_state("google")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Google 授权回调"""
    frontend_base = _get_frontend_base(request)

    if error or not code or not state:
        return RedirectResponse(url=f"{frontend_base}/login?oauth_error=denied")

    provider = _verify_state(state)
    if provider != "google":
        return RedirectResponse(url=f"{frontend_base}/login?oauth_error=invalid_state")

    try:
        frontend_base = _get_frontend_base(request)
        if GOOGLE_REDIRECT_URI:
            redirect_uri = GOOGLE_REDIRECT_URI
        else:
            redirect_uri = f"{frontend_base}/api/auth/google/callback"

        # 用 code 换 token
        import httpx
        async with _get_httpx_client() as client:
            token_resp = await client.post(GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            })
            token_data = token_resp.json()

        access_token = token_data.get("access_token")
        if not access_token:
            logger.error(f"[Google] token error: {token_data}")
            return RedirectResponse(url=f"{frontend_base}/login?oauth_error=token_failed")

        # 获取用户信息
        async with _get_httpx_client() as client:
            userinfo_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_info = userinfo_resp.json()

        google_user_id = user_info.get("id", "")
        email = user_info.get("email", "")
        nickname = user_info.get("name", "")
        avatar = user_info.get("picture", "")

        if not google_user_id:
            return RedirectResponse(url=f"{frontend_base}/login?oauth_error=no_userinfo")

        # 查找/创建用户
        user = _find_or_create_oauth_user(
            db=db, provider="google", provider_user_id=google_user_id,
            email=email, nickname=nickname, avatar_url=avatar,
        )
        return _make_token_response(user, frontend_base)

    except Exception as e:
        logger.error(f"[OAuth] Google callback error: {e}", exc_info=True)
        return RedirectResponse(url=f"{frontend_base}/login?oauth_error=server_error")
