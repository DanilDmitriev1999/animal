"""
// AICODE-NOTE: База для инструментов.
"""

from __future__ import annotations

from typing import Any, Type
from pydantic import BaseModel


class ToolBase:
    id: str = ""
    version: str = ""
    input_schema: Type[BaseModel] | None = None
    output_schema: Type[BaseModel] | None = None

    def __init__(self, memory=None) -> None:
        self.memory = memory

    async def run(self, **kwargs) -> Any:  # pragma: no cover - интерфейс
        raise NotImplementedError


__all__ = ["ToolBase"]


