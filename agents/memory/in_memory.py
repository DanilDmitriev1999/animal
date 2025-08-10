"""
// AICODE-NOTE: InMemoryMemory — простая in-memory реализация для локальных запусков и CLI.
"""

from __future__ import annotations

from typing import Any, DefaultDict
from collections import defaultdict


class InMemoryMemory:
    def __init__(self) -> None:
        self._messages: DefaultDict[str, list[dict]] = defaultdict(list)
        self._kv: DefaultDict[str, dict[str, Any]] = defaultdict(dict)

    async def load_dialog(self, session_id: str, role_policy: dict) -> list[dict]:
        return list(self._messages[session_id])

    async def append(self, session_id: str, messages: list[dict]) -> None:
        self._messages[session_id].extend(messages)

    async def set_kv(self, session_id: str, key: str, value: Any) -> None:
        self._kv[session_id][key] = value

    async def get_kv(self, session_id: str, key: str) -> Any:
        return self._kv[session_id].get(key)


__all__ = ["InMemoryMemory"]


