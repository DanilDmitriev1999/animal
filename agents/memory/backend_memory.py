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
        # Определяем вкладку из политики роли; по умолчанию используем chat
        tab = str(role_policy.get("tab", "chat"))
        if tab not in {"chat", "practice", "simulation"}:
            tab = "chat"
        r = await self.client.get(f"/sessions/{session_id}/messages/{tab}")
        r.raise_for_status()
        messages = r.json()
        # API возвращает массив Message {role, content, ...}; уже готово к прокидке в LLM
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    async def append(self, session_id: str, messages: list[dict]) -> None:
        # Запишем как assistant‑сообщения. Учитываем вкладку из политики роли (если была сохранена через set_kv).
        # Для простоты — используем chat по умолчанию.
        tab = "chat"
        try:
            # Попытка получить таб из KV (если агент сохранил его заранее)
            # KV не реализован в BackendMemory, поэтому оставим chat.
            pass
        except Exception:
            pass
        for m in messages:
            role = m.get("role", "assistant")
            content = m.get("content", "")
            if isinstance(content, dict):
                # Если пришла форма {"message": "..."} — извлекаем строку
                content = content.get("message", "")
            body = {"role": role, "content": str(content), "meta": m.get("meta")}
            r = await self.client.post(f"/sessions/{session_id}/messages/{tab}", json=body)
            r.raise_for_status()

    async def set_kv(self, session_id: str, key: str, value: Any) -> None:  # pragma: no cover — пока не требуется
        return

    async def get_kv(self, session_id: str, key: str) -> Any:  # pragma: no cover — пока не требуется
        return None


