import logging
from typing import Optional
from urllib.parse import urlencode

import httpx

from .config import OAuthConfig

logger = logging.getLogger(__name__)

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleOAuthClient:
    def __init__(self, config: OAuthConfig):
        self._config = config
        self._httpx_kwargs: dict = {"timeout": 15.0}
        if config.http_proxy:
            self._httpx_kwargs["proxy"] = config.http_proxy

    def build_authorize_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self._config.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{AUTH_URL}?{urlencode(params)}"

    async def exchange_token(self, code: str, redirect_uri: str) -> Optional[dict]:
        """用 code 换 access_token，返回 token dict 或 None"""
        try:
            async with httpx.AsyncClient(**self._httpx_kwargs) as client:
                resp = await client.post(TOKEN_URL, data={
                    "code": code,
                    "client_id": self._config.google_client_id,
                    "client_secret": self._config.google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                })
                data = resp.json()

            if not data.get("access_token"):
                logger.error(f"[Google] token error: {data}")
                return None
            return data
        except Exception as e:
            logger.error(f"[Google] token exception: {e}", exc_info=True)
            return None

    async def get_user_info(self, access_token: str) -> Optional[dict]:
        """获取 Google 用户信息"""
        try:
            async with httpx.AsyncClient(**self._httpx_kwargs) as client:
                resp = await client.get(
                    USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                return resp.json()
        except Exception as e:
            logger.error(f"[Google] userinfo exception: {e}", exc_info=True)
            return None
