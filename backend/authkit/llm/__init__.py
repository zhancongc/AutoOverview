"""
authkit.llm — LLM 客户端统一管理

用法:
    from authkit.llm import get_llm_client

    # 获取原始 AsyncOpenAI 客户端（渐进式迁移）
    client = get_llm_client().get_raw_client()
    response = await client.chat.completions.create(...)

    # 使用高级封装
    result = await get_llm_client().chat(messages=[...])
"""
import logging
from typing import Optional

from .config import LLMConfig
from .client import LLMClient

logger = logging.getLogger(__name__)

_default_client: Optional[LLMClient] = None


def create_llm_client(config: LLMConfig = None) -> LLMClient:
    """创建 LLM 客户端。config 为空时从环境变量读取。"""
    return LLMClient(config)


def get_llm_client() -> Optional[LLMClient]:
    """获取全局单例 LLM 客户端。如未初始化会自动创建。"""
    global _default_client
    if _default_client is None:
        _default_client = create_llm_client()
    return _default_client


__all__ = [
    "LLMConfig",
    "LLMClient",
    "create_llm_client",
    "get_llm_client",
]
