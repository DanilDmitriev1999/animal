"""
// AICODE-NOTE: Минимальный CallbackManager с каналами before/after.
"""

from __future__ import annotations

from typing import Callable, Dict, DefaultDict
from collections import defaultdict


class CallbackManager:
    def __init__(self) -> None:
        self._handlers: DefaultDict[str, Dict[str, list[Callable[..., None]]]] = defaultdict(lambda: defaultdict(list))

    def register(self, moment: str, kind: str, handler: Callable[..., None]) -> None:
        self._handlers[moment][kind].append(handler)

    def fire(self, moment: str, kind: str, **kwargs) -> None:
        for h in self._handlers[moment][kind]:
            h(**kwargs)


callbacks = CallbackManager()


__all__ = ["callbacks", "CallbackManager"]


