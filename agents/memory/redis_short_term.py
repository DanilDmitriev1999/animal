"""
// AICODE-NOTE: Короткая память на Redis. Простая обёртка, безопасная по умолчанию.
"""

from __future__ import annotations

import os
import json
from typing import Any

try:
    import redis  # type: ignore
except Exception as e:  # pragma: no cover
    redis = None  # type: ignore


class RedisShortTerm:
    def __init__(self, url: str | None = None, max_messages: int = 50) -> None:
        if redis is None:
            raise RuntimeError("redis-py is not installed")
        self.client = redis.from_url(url or os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        self.max_messages = max_messages

    async def load_dialog(self, session_id: str, role_policy: dict) -> list[dict]:
        key = f"chat:{session_id}"
        data = self.client.lrange(key, 0, self.max_messages)
        return [json.loads(x) for x in data[::-1]]

    async def append(self, session_id: str, messages: list[dict]) -> None:
        key = f"chat:{session_id}"
        pipe = self.client.pipeline()
        for m in messages:
            pipe.lpush(key, json.dumps(m))
        pipe.ltrim(key, 0, self.max_messages - 1)
        pipe.execute()

    async def set_kv(self, session_id: str, key: str, value: Any) -> None:
        self.client.hset(f"session:{session_id}", key, json.dumps(value))

    async def get_kv(self, session_id: str, key: str) -> Any:
        raw = self.client.hget(f"session:{session_id}", key)
        return json.loads(raw) if raw else None


__all__ = ["RedisShortTerm"]


