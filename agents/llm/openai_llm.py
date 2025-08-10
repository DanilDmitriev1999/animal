"""
// AICODE-NOTE: Реализация LLMClientABC для OpenAI SDK.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional, Sequence
from pydantic import BaseModel
from .base import LLMClientBase, LLMMessage, LLMResponse, LLMTool


from openai import OpenAI  # type: ignore

class OpenAILLM(LLMClientBase):
    def __init__(self, *, default_model: Optional[str] = None, **client_kwargs: Any) -> None:
        super().__init__(default_model=default_model, **client_kwargs)

    def _create_client(self, **client_kwargs: Any) -> Any:
        # client_kwargs: api_key, base_url и т.д.
        return OpenAI(**client_kwargs)

    async def chat(
        self,
        messages: Sequence[LLMMessage],
        *,
        model: Optional[str] = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        mdl = model or self._default_model
        resp = self._client.chat.completions.create(
            model=mdl,
            messages=list(messages),
            temperature=temperature if temperature is not None else 0.3,
        )
        text = resp.choices[0].message.content
        return LLMResponse(result=text, client_response=resp)

    async def structured_output(
        self,
        messages: Sequence[LLMMessage],
        *,
        schema: BaseModel | Dict[str, Any],
        model: Optional[str] = None,
    ) -> tuple[Any, LLMResponse]:
        mdl = model or self._default_model
        resp = self._client.beta.chat.completions.parse(
            model=mdl,
            messages=list(messages),
            response_format=schema
        )
        parsed = json.loads(resp.choices[0].message.content)
        # не использую message.parsed, так как это не корретно работает с json схемой, но с pydantic все норм

        return LLMResponse(result=parsed, client_response=resp)

    async def chat_with_tools(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[LLMTool],
        *,
        model: Optional[str] = None,
        temperature: float | None = None,
        max_steps: int = 3,
    ) -> LLMResponse:
        text = ""
        resp = None
        return LLMResponse(text=text, client_response=resp)

    async def vision_analyze(
        self,
        *,
        prompt: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        text = ""
        resp = None
        return LLMResponse(text=text, client_response=resp)


__all__ = ["OpenAILLM"]


