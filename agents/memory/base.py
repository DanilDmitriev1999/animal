"""
// AICODE-NOTE: Контракт памяти. Минимальная протокол‑обвязка.
"""

from __future__ import annotations

from typing import Any, Protocol


class BaseMemory(Protocol):
    async def load_dialog(self, session_id: str, role_policy: dict) -> list[dict]: ...
    async def append(self, session_id: str, messages: list[dict]) -> None: ...
    async def set_kv(self, session_id: str, key: str, value: Any) -> None: ...
    async def get_kv(self, session_id: str, key: str) -> Any: ...


__all__ = ["BaseMemory"]


