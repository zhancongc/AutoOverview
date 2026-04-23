from typing import Any, Protocol

from fastapi import Request
from fastapi.responses import RedirectResponse


class FindOrCreateUser(Protocol):
    async def __call__(
        self,
        *,
        provider: str,
        provider_user_id: str,
        email: str,
        nickname: str,
        avatar_url: str,
    ) -> Any: ...


class MakeTokenResponse(Protocol):
    async def __call__(self, user: Any, frontend_base: str) -> RedirectResponse: ...


class GetFrontendBase(Protocol):
    def __call__(self, request: Request) -> str: ...
