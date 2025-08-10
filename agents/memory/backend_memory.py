"""
// AICODE-NOTE: BackendMemory — грузит/дополняет диалог через REST API бэкенда.
// Контракты эндпоинтов см. в backend/API.md.
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class BackendMemory:
    def __init__(self, base_url: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.base_url = base_url or os.getenv("AGENTS_BACKEND_API_URL", "http://localhost:8000")
        self.client = client or httpx.AsyncClient(base_url=self.base_url, timeout=15)

    async def load_dialog(self, session_id: str, role_policy: dict) -> list[dict]:
        # Загружаем три ветки и склеиваем: chat, practice, simulation — пока достаточно chat
        # Минимально берём чат вкладку
        r = await self.client.get(f"/sessions/{session_id}/messages/chat")
        r.raise_for_status()
        messages = r.json()
        # API возвращает массив Message {role, content, ...}; уже готово к прокидке в LLM
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    async def append(self, session_id: str, messages: list[dict]) -> None:
        # Запишем как assistant‑сообщения в ветку chat (простая стратегия)
        for m in messages:
            body = {"role": m.get("role", "assistant"), "content": m.get("content", ""), "meta": m.get("meta")}
            r = await self.client.post(f"/sessions/{session_id}/messages/chat", json=body)
            r.raise_for_status()

    async def set_kv(self, session_id: str, key: str, value: Any) -> None:  # pragma: no cover — пока не требуется
        return

    async def get_kv(self, session_id: str, key: str) -> Any:  # pragma: no cover — пока не требуется
        return None


