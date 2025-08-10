"""
// AICODE-NOTE: Базовые протоколы Event и AgentBase (минимум для запуска).
// AICODE-NOTE: Добавлен абстрактный базовый класс AgentABC для единообразного контракта.
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol, Any, Dict, TYPE_CHECKING
from abc import ABC, abstractmethod
from pydantic import BaseModel

if TYPE_CHECKING:  # pragma: no cover - для аннотаций
    from .memory.base import BaseMemory


class Event(BaseModel):
    event: str
    session_id: str
    trace_id: str
    payload: Dict[str, Any] | None = None


class AgentBase(Protocol):
    id: str
    version: str
    memory: "BaseMemory"
    role_policy: dict
    meta: dict

    async def run(self, **kwargs) -> dict: ...
    async def run_with_events(self, **kwargs) -> AsyncIterator[Event]: ...


class AgentABC(ABC):
    """Абстрактный базовый класс агента с фиксированным контрактом событий.

    Обеспечивает:
    - единый запуск `run()` поверх `run_with_events()`;
    - авто-событие `start_agent` и гарантию финального `final_result` (если не сгенерирован);
    - хелпер `emit()` для создания событий.
    """

    # AICODE-NOTE: Класс предназначен для наследования паттернами и конкретными агентами.

    id: str = "base"
    version: str = "v1"

    def __init__(self, memory: "BaseMemory", *, role_policy: dict | None = None, meta: dict | None = None, llm: Any | None = None) -> None:
        self.memory = memory
        self.role_policy = role_policy or {}
        self.meta = meta or {}
        # AICODE-NOTE: LLM должен задаваться при инициализации агента; конкретная реализация (клиент/фасад)
        # прокидывается через этот атрибут. Наследники могут полагаться на `self.llm`.
        self.llm = llm

    def emit(self, event: str, session_id: str, *, payload: Dict[str, Any] | None = None, trace_id: str = "") -> Event:
        return Event(event=event, session_id=session_id, trace_id=trace_id, payload=payload)

    async def run(self, **kwargs) -> dict:
        async for _ in self.run_with_events(**kwargs):
            pass
        return {"ok": True}

    async def run_with_events(self, *, session_id: str, **ctx) -> AsyncIterator[Event]:
        # Стартовое событие — единообразно для всех наследников
        yield self.emit("start_agent", session_id, payload={"agent": self.id, "version": self.version})
        final_emitted = False
        async for ev in self._run(session_id=session_id, **ctx):
            if ev.event == "final_result":
                final_emitted = True
            yield ev
        if not final_emitted:
            # Гарантируем финальное событие (минимальное)
            yield self.emit("final_result", session_id, payload={"ok": True})

    @abstractmethod
    async def _run(self, *, session_id: str, **ctx) -> AsyncIterator[Event]:  # pragma: no cover - реализуется наследниками
        """Реализация бизнес-логики агента c генерацией событий.

        Должна yield'ить события и, как правило, завершаться событием `final_result`.
        """
        raise NotImplementedError


__all__ = ["Event", "AgentBase", "AgentABC"]


