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

import httpx

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


def _load_alipay_key(env_val: str, default_path: str, is_private: bool = True) -> str:
    """加载支付宝密钥：优先用 env 变量值，否则从文件读取，自动补 PEM 头"""
    if env_val:
        return env_val
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    full_path = os.path.join(base_dir, default_path)
    if os.path.exists(full_path):
        with open(full_path, "r") as f:
            key = f.read().strip()

        # 裸 base64 没有 PEM 头，自动补上
        if "BEGIN" not in key:
            if is_private:
                # PKCS#8 私钥
                key = f"-----BEGIN PRIVATE KEY-----\n{key}\n-----END PRIVATE KEY-----"
            else:
                key = f"-----BEGIN PUBLIC KEY-----\n{key}\n-----END PUBLIC KEY-----"

        # PKCS#8 私钥转 PKCS#1（cryptography 兼容）
        if is_private and "BEGIN PRIVATE KEY" in key and "BEGIN RSA PRIVATE KEY" not in key:
            try:
                from cryptography.hazmat.primitives.serialization import load_pem_private_key, Encoding, PrivateFormat, NoEncryption
                private_key = load_pem_private_key(key.encode(), password=None)
                key = private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()).decode()
            except Exception as e:
                logger.warning(f"[Alipay] PKCS8→PKCS1 转换失败: {e}")
        return key
    return ""


ALIPAY_PRIVATE_KEY = _load_alipay_key(os.getenv("ALIPAY_PRIVATE_KEY", ""), "app_secrets.txt", is_private=True)
ALIPAY_PUBLIC_KEY = _load_alipay_key(os.getenv("ALIPAY_PUBLIC_KEY", ""), "alipay_public_key.txt", is_private=False)


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
        open_id = token_data.get("open_id")

        # 获取用户信息（即使失败也不影响登录）
        user_info = _alipay_get_user_info(access_token, open_id)
        nickname = user_info.get("nick_name", "")
        avatar = user_info.get("avatar", "")

        # 查找/创建用户
        user = _find_or_create_oauth_user(
            db=db, provider="alipay", provider_user_id=open_id,
            email="", nickname=nickname, avatar_url=avatar,
        )
        return _make_token_response(user, frontend_base)

    except Exception as e:
        logger.error(f"[OAuth] Alipay callback error: {e}", exc_info=True)
        return RedirectResponse(url=f"{frontend_base}/login?oauth_error=server_error")


def _patch_alipay_signing():
    """
    用 cryptography 替换 rsa 库做签名，绕过 pyasn1 兼容性问题。
    参考 gongkao 项目：rsa 4.9.1 + pyasn1 0.6.1 可正常工作，
    但生产环境依赖版本可能不一致，直接用 cryptography 更可靠。
    """
    import base64
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    import alipay.aop.api.util.SignatureUtils as su

    _orig_sign = su.sign_with_rsa2

    def _sign_with_cryptography(private_key_pem, sign_content, charset):
        if isinstance(sign_content, str):
            sign_content = sign_content.encode(charset or "utf-8")
        if isinstance(private_key_pem, str):
            private_key_pem = private_key_pem.encode("utf-8")
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)
        signature = private_key.sign(sign_content, padding.PKCS1v15(), hashes.SHA256())
        return base64.b64encode(signature).decode("ascii")

    su.sign_with_rsa2 = _sign_with_cryptography
    logger.info("[Alipay] 已替换 sign_with_rsa2 为 cryptography 实现")


# 模块加载时 patch 一次
_patch_alipay_signing()


def _get_alipay_client():
    """创建支付宝客户端（官方 SDK: alipay-sdk-python）"""
    from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
    from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient

    config = AlipayClientConfig()
    config.app_id = ALIPAY_APP_ID
    config.app_private_key = ALIPAY_PRIVATE_KEY
    config.alipay_public_key = ALIPAY_PUBLIC_KEY
    config.sign_type = "RSA2"
    return DefaultAlipayClient(config, logger)


def _alipay_get_token(auth_code: str) -> dict:
    """用 auth_code 换 access_token"""
    try:
        client = _get_alipay_client()
        from alipay.aop.api.request.AlipaySystemOauthTokenRequest import AlipaySystemOauthTokenRequest

        request = AlipaySystemOauthTokenRequest()
        request.code = auth_code
        request.grant_type = "authorization_code"

        response_content = client.execute(request)
        logger.info(f"[Alipay] get_token raw response: {response_content}")

        # SDK 3.7.1018 的 execute() 已提取内层 JSON，直接解析
        data = json.loads(response_content) if isinstance(response_content, str) else response_content
        access_token = data.get("access_token")
        open_id = data.get("open_id") or data.get("user_id")

        if access_token and open_id:
            return {"access_token": access_token, "open_id": open_id}

        error = data.get("error_response", {})
        logger.error(f"[Alipay] get_token failed: {error}")
        return {}
    except Exception as e:
        logger.error(f"[Alipay] get_token exception: {e}", exc_info=True)
        return {}


def _alipay_get_user_info(access_token: str, open_id: str) -> dict:
    """获取支付宝用户信息"""
    try:
        client = _get_alipay_client()
        from alipay.aop.api.request.AlipayUserInfoShareRequest import AlipayUserInfoShareRequest

        request = AlipayUserInfoShareRequest()

        response_content = client.execute(request, access_token)
        logger.info(f"[Alipay] user_info raw response: {response_content}")

        data = json.loads(response_content) if isinstance(response_content, str) else response_content

        # 检查是否有错误
        if "error_response" in data and isinstance(data, dict):
            logger.error(f"[Alipay] user_info failed: {data['error_response']}")
            return {"open_id": open_id, "nick_name": "", "avatar": ""}

        nick_name = data.get("nick_name", "")
        avatar = data.get("avatar", "")

        if nick_name or avatar:
            return {"open_id": open_id, "nick_name": nick_name, "avatar": avatar}

        # 用户信息获取失败也返回 open_id，不影响登录
        return {"open_id": open_id, "nick_name": "", "avatar": ""}
    except Exception as e:
        logger.error(f"[Alipay] user_info exception: {e}", exc_info=True)
        return {"open_id": open_id, "nick_name": "", "avatar": ""}


# ==================== Google 登录 ====================

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# 生产服务器走本地 SOCKS5 代理访问 Google
HTTP_PROXY = os.getenv("HTTP_PROXY", "socks5://127.0.0.1:1080") or os.getenv("http_proxy", "")


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
