import base64
import json
import logging
import os
from typing import Optional
from urllib.parse import urlencode

from .config import OAuthConfig

logger = logging.getLogger(__name__)


def _patch_signing():
    """用 cryptography 替换 rsa 库做签名，绕过 pyasn1 兼容性问题"""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    import alipay.aop.api.util.SignatureUtils as su

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


def _load_key(env_val: str, file_path: str, base_dir: str, is_private: bool = True) -> str:
    """加载密钥：优先 env 变量，否则从文件读取，自动补 PEM 头并转 PKCS#1"""
    key = ""

    if env_val:
        key = env_val.strip()
    elif file_path:
        search_dir = base_dir or os.getcwd()
        full_path = os.path.join(search_dir, file_path)
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                key = f.read().strip()

    if not key:
        return ""

    # 裸 base64 没有 PEM 头，自动补上
    if "BEGIN" not in key:
        if is_private:
            key = f"-----BEGIN PRIVATE KEY-----\n{key}\n-----END PRIVATE KEY-----"
        else:
            key = f"-----BEGIN PUBLIC KEY-----\n{key}\n-----END PUBLIC KEY-----"

    # PKCS#8 私钥转 PKCS#1
    if is_private and "BEGIN PRIVATE KEY" in key and "BEGIN RSA PRIVATE KEY" not in key:
        try:
            from cryptography.hazmat.primitives.serialization import (
                load_pem_private_key, Encoding, PrivateFormat, NoEncryption,
            )
            pk = load_pem_private_key(key.encode(), password=None)
            key = pk.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()).decode()
        except Exception as e:
            logger.warning(f"[Alipay] PKCS8→PKCS1 转换失败: {e}")

    return key


class AlipayOAuthClient:
    def __init__(self, config: OAuthConfig):
        self._config = config
        self._private_key = _load_key(
            config.alipay_private_key, config.alipay_private_key_path,
            config.alipay_base_dir, is_private=True,
        )
        self._public_key = _load_key(
            config.alipay_public_key, config.alipay_public_key_path,
            config.alipay_base_dir, is_private=False,
        )
        _patch_signing()

    def build_authorize_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "app_id": self._config.alipay_app_id,
            "redirect_uri": redirect_uri,
            "scope": "auth_user",
            "state": state,
            "response_type": "code",
        }
        return f"https://openauth.alipay.com/oauth2/publicAppAuthorize.htm?{urlencode(params)}"

    def exchange_token(self, auth_code: str) -> Optional[dict]:
        """用 auth_code 换 access_token，返回 {access_token, open_id} 或 None"""
        try:
            from alipay.aop.api.request.AlipaySystemOauthTokenRequest import AlipaySystemOauthTokenRequest
            client = self._get_sdk_client()

            request = AlipaySystemOauthTokenRequest()
            request.code = auth_code
            request.grant_type = "authorization_code"

            response_content = client.execute(request)
            logger.info(f"[Alipay] get_token response: {response_content}")

            data = json.loads(response_content) if isinstance(response_content, str) else response_content
            access_token = data.get("access_token")
            open_id = data.get("open_id") or data.get("user_id")

            if access_token and open_id:
                return {"access_token": access_token, "open_id": open_id}

            error = data.get("error_response", {})
            logger.error(f"[Alipay] get_token failed: {error}")
            return None
        except Exception as e:
            logger.error(f"[Alipay] get_token exception: {e}", exc_info=True)
            return None

    def get_user_info(self, access_token: str, open_id: str) -> dict:
        """获取支付宝用户信息，失败不影响登录"""
        try:
            from alipay.aop.api.request.AlipayUserInfoShareRequest import AlipayUserInfoShareRequest
            client = self._get_sdk_client()

            request = AlipayUserInfoShareRequest()
            response_content = client.execute(request, access_token)
            logger.info(f"[Alipay] user_info response: {response_content}")

            data = json.loads(response_content) if isinstance(response_content, str) else response_content

            if "error_response" in data:
                logger.error(f"[Alipay] user_info failed: {data['error_response']}")
                return {"open_id": open_id, "nick_name": "", "avatar": ""}

            return {
                "open_id": open_id,
                "nick_name": data.get("nick_name", ""),
                "avatar": data.get("avatar", ""),
            }
        except Exception as e:
            logger.error(f"[Alipay] user_info exception: {e}", exc_info=True)
            return {"open_id": open_id, "nick_name": "", "avatar": ""}

    def _get_sdk_client(self):
        from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
        from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient

        config = AlipayClientConfig()
        config.app_id = self._config.alipay_app_id
        config.app_private_key = self._private_key
        config.alipay_public_key = self._public_key
        config.sign_type = "RSA2"
        return DefaultAlipayClient(config, logger)
