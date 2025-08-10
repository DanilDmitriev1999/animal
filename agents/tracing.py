"""
// AICODE-NOTE: Интерфейс трейсинга. Фактическую запись делает бэкенд через адаптеры.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .base import Event


@dataclass
class Trace:
    id: uuid.UUID
    entity_type: str
    entity_id: str
    version: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "running"

    @staticmethod
    def start(entity_type: str, entity_id: str, version: str, payload: dict | None = None) -> "Trace":
        # AICODE-NOTE: В минимальной версии просто возвращаем объект; бэкенд‑интеграция добавится позже
        return Trace(id=uuid.uuid4(), entity_type=entity_type, entity_id=entity_id, version=version, payload=payload or {})

    @staticmethod
    def event(trace: "Trace", ev: Event) -> None:
        # AICODE-NOTE: Хук для записи событий в БД через бэкенд (будет добавлено позже)
        return

    @staticmethod
    def finish(trace: "Trace", status: str = "success") -> None:
        trace.status = status
        return


__all__ = ["Trace"]


