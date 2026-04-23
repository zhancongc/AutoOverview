from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OAuthConfig:
    # Alipay
    alipay_app_id: str = ""
    alipay_private_key: str = ""
    alipay_public_key: str = ""
    alipay_private_key_path: str = ""
    alipay_public_key_path: str = ""
    alipay_base_dir: str = ""  # 密钥文件查找的基础目录，为空则用 CWD

    # Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""

    # 通用
    http_proxy: str = ""
    state_ttl_seconds: int = 600

    @property
    def alipay_enabled(self) -> bool:
        return bool(self.alipay_app_id)

    @property
    def google_enabled(self) -> bool:
        return bool(self.google_client_id)
