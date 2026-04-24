"""
LLM 客户端 — 统一封装 AsyncOpenAI

提供两种使用方式:
1. get_raw_client() — 返回原始 AsyncOpenAI 实例，适合渐进式迁移
2. chat() / chat_stream() — 高级封装，简化调用
"""
import logging
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from .config import LLMConfig

logger = logging.getLogger(__name__)


class LLMClient:
    """统一的 LLM 客户端"""

    def __init__(self, config: LLMConfig = None):
        self._config = config or LLMConfig()
        self._client = AsyncOpenAI(
            api_key=self._config.api_key,
            base_url=self._config.base_url,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )

    @property
    def config(self) -> LLMConfig:
        return self._config

    def get_raw_client(self) -> AsyncOpenAI:
        """返回底层 AsyncOpenAI 实例，用于渐进式迁移"""
        return self._client

    async def chat(
        self,
        messages: list[dict],
        *,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = None,
        response_format: dict = None,
    ) -> str:
        """高级 chat 接口，返回文本内容"""
        kwargs = {
            "model": model or self._config.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if response_format:
            kwargs["response_format"] = response_format

        response = await self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def chat_json(
        self,
        messages: list[dict],
        *,
        model: str = "",
        temperature: float = 0.3,
        max_tokens: int = None,
    ) -> str:
        """以 JSON 格式请求 chat"""
        return await self.chat(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
