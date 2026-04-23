import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from .config import OAuthConfig
from .protocols import FindOrCreateUser, GetFrontendBase, MakeTokenResponse
from .state import StateManager

logger = logging.getLogger(__name__)


def create_oauth_router(
    *,
    config: OAuthConfig,
    find_or_create_user: FindOrCreateUser,
    make_token_response: MakeTokenResponse,
    get_frontend_base: GetFrontendBase,
    redis_client: Optional[Any] = None,
    prefix: str = "/api/auth",
) -> APIRouter:
    """创建 OAuth 登录路由（Alipay + Google）"""
    router = APIRouter(prefix=prefix, tags=["OAuth 登录"])

    state_mgr = StateManager(
        redis_client=redis_client,
        ttl_seconds=config.state_ttl_seconds,
    )
    router.state_mgr = state_mgr  # 允许外部更新 redis_client

    # 延迟初始化客户端（避免 import 时就要求依赖）
    alipay_client = None
    google_client = None

    def _get_alipay():
        nonlocal alipay_client
        if alipay_client is None and config.alipay_enabled:
            from .alipay import AlipayOAuthClient
            alipay_client = AlipayOAuthClient(config)
        return alipay_client

    def _get_google():
        nonlocal google_client
        if google_client is None and config.google_enabled:
            from .google import GoogleOAuthClient
            google_client = GoogleOAuthClient(config)
        return google_client

    # ==================== 支付宝 ====================

    @router.get("/alipay/authorize")
    async def alipay_authorize(request: Request):
        client = _get_alipay()
        if not client:
            raise HTTPException(status_code=500, detail="支付宝登录未配置")

        frontend_base = get_frontend_base(request)
        redirect_uri = f"{frontend_base}{prefix}/alipay/callback"
        state = state_mgr.generate("alipay")
        return RedirectResponse(url=client.build_authorize_url(redirect_uri, state))

    @router.get("/alipay/callback")
    async def alipay_callback(
        auth_code: Optional[str] = None,
        code: Optional[str] = None,
        state: Optional[str] = None,
        request: Request = None,
    ):
        client = _get_alipay()
        frontend_base = get_frontend_base(request)

        code_val = auth_code or code
        if not code_val or not state:
            return RedirectResponse(url=f"{frontend_base}/login?oauth_error=denied")

        provider = state_mgr.verify(state)
        if provider != "alipay":
            return RedirectResponse(url=f"{frontend_base}/login?oauth_error=invalid_state")

        try:
            token_data = client.exchange_token(code_val)
            if not token_data:
                return RedirectResponse(url=f"{frontend_base}/login?oauth_error=token_failed")

            user_info = client.get_user_info(
                token_data["access_token"], token_data["open_id"],
            )

            user = await find_or_create_user(
                provider="alipay",
                provider_user_id=token_data["open_id"],
                email="",
                nickname=user_info.get("nick_name", ""),
                avatar_url=user_info.get("avatar", ""),
            )
            return await make_token_response(user, frontend_base)

        except Exception as e:
            logger.error(f"[OAuth] Alipay callback error: {e}", exc_info=True)
            return RedirectResponse(url=f"{frontend_base}/login?oauth_error=server_error")

    # ==================== Google ====================

    @router.get("/google/authorize")
    async def google_authorize(request: Request):
        client = _get_google()
        if not client:
            raise HTTPException(status_code=500, detail="Google 登录未配置")

        if config.google_redirect_uri:
            redirect_uri = config.google_redirect_uri
        else:
            frontend_base = get_frontend_base(request)
            redirect_uri = f"{frontend_base}{prefix}/google/callback"

        state = state_mgr.generate("google")
        return RedirectResponse(url=client.build_authorize_url(redirect_uri, state))

    @router.get("/google/callback")
    async def google_callback(
        code: Optional[str] = None,
        state: Optional[str] = None,
        error: Optional[str] = None,
        request: Request = None,
    ):
        client = _get_google()
        frontend_base = get_frontend_base(request)

        if error or not code or not state:
            return RedirectResponse(url=f"{frontend_base}/login?oauth_error=denied")

        provider = state_mgr.verify(state)
        if provider != "google":
            return RedirectResponse(url=f"{frontend_base}/login?oauth_error=invalid_state")

        try:
            if config.google_redirect_uri:
                redirect_uri = config.google_redirect_uri
            else:
                redirect_uri = f"{get_frontend_base(request)}{prefix}/google/callback"

            token_data = await client.exchange_token(code, redirect_uri)
            if not token_data:
                return RedirectResponse(url=f"{frontend_base}/login?oauth_error=token_failed")

            access_token = token_data.get("access_token")
            if not access_token:
                return RedirectResponse(url=f"{frontend_base}/login?oauth_error=token_failed")

            user_info = await client.get_user_info(access_token)
            if not user_info or not user_info.get("id"):
                return RedirectResponse(url=f"{frontend_base}/login?oauth_error=no_userinfo")

            user = await find_or_create_user(
                provider="google",
                provider_user_id=user_info.get("id", ""),
                email=user_info.get("email", ""),
                nickname=user_info.get("name", ""),
                avatar_url=user_info.get("picture", ""),
            )
            return await make_token_response(user, frontend_base)

        except Exception as e:
            logger.error(f"[OAuth] Google callback error: {e}", exc_info=True)
            return RedirectResponse(url=f"{frontend_base}/login?oauth_error=server_error")

    return router
