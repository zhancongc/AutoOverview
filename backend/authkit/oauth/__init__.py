"""
authkit.oauth -- 可复用的 OAuth 登录模块（Alipay + Google）
"""
from .config import OAuthConfig
from .protocols import FindOrCreateUser, GetFrontendBase, MakeTokenResponse
from .router import create_oauth_router

__all__ = [
    "OAuthConfig",
    "create_oauth_router",
    "FindOrCreateUser",
    "MakeTokenResponse",
    "GetFrontendBase",
]
