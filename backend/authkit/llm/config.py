"""
LLM 配置
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMConfig:
    """LLM 客户端配置。所有字段默认从环境变量读取。"""
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    timeout: float = 120.0
    max_retries: int = 3

    def __post_init__(self):
        if not self.api_key:
            object.__setattr__(self, 'api_key', os.getenv("DEEPSEEK_API_KEY", ""))
        if not self.base_url:
            object.__setattr__(self, 'base_url', os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
        if not self.model:
            object.__setattr__(self, 'model', os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
