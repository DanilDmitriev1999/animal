"""
// AICODE-NOTE: Базовые интерфейсы для LLM-абстракции.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol, Sequence
from abc import ABC, abstractmethod

try:
    from pydantic import BaseModel
except Exception:  # pragma: no cover - pydantic опционален для структурных ответов
    BaseModel = object  # type: ignore


LLMMessage = Dict[str, Any]


@dataclass
class LLMResponse:
    result: str | dict
    client_response: Any | None = None


class LLMTool(Protocol):  # pragma: no cover - протокол для IDE/типов
    name: str
    description: str
    parameters: Dict[str, Any]

    def __call__(self, **kwargs: Any) -> Any | Awaitable[Any]: ...

class LLMClientBase(ABC):
    """Абстрактный базовый LLM‑клиент.

    Создаёт внутренний SDK‑клиент через `_create_client()` в конструкторе.
    Наследники реализуют `_create_client()` и публичные методы.
    """

    def __init__(self, *, default_model: Optional[str] = None, **client_kwargs: Any) -> None:
        self._default_model = default_model
        self._client = self._create_client(**client_kwargs)

    @abstractmethod
    def _create_client(self, **client_kwargs: Any) -> Any: ...

    @abstractmethod
    async def chat(
        self,
        messages: Sequence[LLMMessage],
        *,
        model: Optional[str] = None,
        temperature: float | None = None,
    ) -> LLMResponse: ...

    @abstractmethod
    async def structured_output(
        self,
        messages: Sequence[LLMMessage],
        *,
        schema: type[Any] | Dict[str, Any],
        model: Optional[str] = None,
        temperature: float | None = None,
    ) -> tuple[Any, LLMResponse]: ...

    @abstractmethod
    async def chat_with_tools(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[LLMTool],
        *,
        model: Optional[str] = None,
        temperature: float | None = None,
        max_steps: int = 3,
    ) -> LLMResponse: ...

    @abstractmethod
    async def vision_analyze(
        self,
        *,
        prompt: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float | None = None,
    ) -> LLMResponse: ...



__all__ = [
    "LLMMessage",
    "LLMResponse",
    "LLMTool",
    "LLMClientBase",
]


