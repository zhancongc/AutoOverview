import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class StateManager:
    redis_client: Optional[Any] = None
    ttl_seconds: int = 600
    _store: dict = field(default_factory=dict)

    def generate(self, provider: str) -> str:
        state = secrets.token_urlsafe(32)
        data = json.dumps({
            "provider": provider,
            "created_at": datetime.utcnow().timestamp(),
        })
        if self.redis_client:
            self.redis_client.setex(f"oauth:state:{state}", self.ttl_seconds, data)
        else:
            self._store[state] = {
                "provider": provider,
                "created_at": datetime.utcnow().timestamp(),
            }
        return state

    def verify(self, state: str) -> Optional[str]:
        if self.redis_client:
            raw = self.redis_client.getdel(f"oauth:state:{state}")
            if not raw:
                return None
            entry = json.loads(raw)
            return entry["provider"]

        entry = self._store.pop(state, None)
        if not entry:
            return None
        elapsed = datetime.utcnow().timestamp() - entry["created_at"]
        if elapsed > self.ttl_seconds:
            return None
        return entry["provider"]
