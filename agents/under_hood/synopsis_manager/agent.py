"""
// AICODE-NOTE: Агент управления конспектом. Умеет создать и обновить конспект.

Сценарии:
- action=create: на вход анкета (`CreateTrackParams`) и финализированный пользователем план (list[str]).
- action=update: на вход анкета, актуальный конспект и изменения/уточнения пользователя (instructions|plan).

Результат: payload с ключом `synopsis` совместимый с фронтом `LiveSynopsis`.
Работает без реального LLM: есть детерминированный fallback‑генератор.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, AsyncIterator

from ...base import AgentABC, Event
from ...registry import register_agent, get_prompt
from ...roles.policy import DialogueBuilder, to_openai_chat_messages

from .so_schema import SynopsisLLMSchema
from ..learning_planner.so_schema import CreateTrackParams


@register_agent("synopsis_manager", "v1")
def factory(memory, role_policy=None, meta=None, llm=None):
    return SynopsisManagerAgent(memory=memory, role_policy=role_policy or {}, meta=meta or {}, llm=llm)


class SynopsisManagerAgent(AgentABC):
    id = "synopsis_manager"
    version = "v1"

    def __init__(self, memory, role_policy=None, meta=None, llm=None):
        super().__init__(memory, role_policy=role_policy, meta=meta, llm=llm)

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    @staticmethod
    def _now_str() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    # ---------------------------------------------------------------------
    async def _run(self, *, session_id: str, query: dict, **_) -> AsyncIterator[Event]:
        # Подготовка контекста
        action = str(query.get("action", "create"))

        # normalize params
        raw_params = query.get("params") or query
        params = CreateTrackParams(**raw_params)
        plan_list = query.get("plan") or []
        prev_synopsis = query.get("synopsis") or []
        instructions = query.get("instructions")

        topic_text = (
            f"Название: {params.title}.\n"
            f"Описание: {params.description}.\n"
            f"Цель: {params.goal}.\n"
            f"Тип обучения: {params.focus}. Тон: {params.tone}."
        )
        plan_text = "\n".join(f"- {p}" for p in plan_list)

        step = "creating_synopsis" if action == "create" else "updating_synopsis"
        yield self.emit(step, session_id, payload={"message": "Готовим конспект"})

        # Попытка через LLM (LLM‑дружественная схема)
        system_text = get_prompt("synopsis_manager.system")
        developer_text = get_prompt("synopsis_manager.developer").format(topic=topic_text, plan=plan_text)
        dialog = await DialogueBuilder.build(
            self.memory, session_id, self.role_policy, step, system_text=system_text, developer_text=developer_text
        )

        model = self.meta.get("model") or os.getenv("AGENTS_DEFAULT_MODEL", "gpt-4.1-mini")
        messages = to_openai_chat_messages(dialog)

        # Совместимо с реализацией в learning_planner; используем упрощённую схему
        response = await self.llm.structured_output(messages=messages, model=model, schema=SynopsisLLMSchema)  # type: ignore[arg-type]
        result = getattr(response, "result", {}) or {}
        if isinstance(result, dict) and not result.get("lastUpdated"):
            result["lastUpdated"] = self._now_str()

        payload: dict[str, Any] = {"synopsis": result, "sources": []}
        await self.memory.append(session_id, [{"role": "assistant", "name": step, "content": payload}])
        yield self.emit("final_result", session_id, payload=payload)


