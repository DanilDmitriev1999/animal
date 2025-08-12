"""
// AICODE-NOTE: Разговорный агент тренера по практике (вкладка «Практика»).
// Отдаёт текстовую подсказку/шаг без структурированного JSON.
"""

from __future__ import annotations

import os
from typing import AsyncIterator

from ...base import AgentABC, Event
from ...registry import register_agent, get_prompt
from ...roles.policy import DialogueBuilder, to_openai_chat_messages


@register_agent("practice_coach", "v1")
def factory(memory, role_policy=None, meta=None, llm=None):
    return PracticeCoachAgent(memory=memory, role_policy=role_policy or {}, meta=meta or {}, llm=llm)


class PracticeCoachAgent(AgentABC):
    id = "practice_coach"
    version = "v1"

    def __init__(self, memory, role_policy=None, meta=None, llm=None):
        super().__init__(memory, role_policy=role_policy, meta=meta, llm=llm)

    async def _run(self, *, session_id: str, user_message: str = "", **_) -> AsyncIterator[Event]:
        step = "practice_hint"
        yield self.emit(step, session_id, payload={"message": "Готовим практический шаг"})

        effective_message = user_message.strip() or "Предложи первый маленький практический шаг по теме курса."

        system_text = get_prompt("practice_coach.system")
        developer_text = get_prompt("practice_coach.developer").format(message=effective_message)
        dialog = await DialogueBuilder.build(
            self.memory,
            session_id,
            self.role_policy,
            step,
            system_text=system_text,
            developer_text=developer_text,
        )

        model = self.meta.get("model") or os.getenv("AGENTS_DEFAULT_MODEL", "gpt-4o-mini")
        messages = to_openai_chat_messages(dialog)
        response = await self.llm.chat(messages=messages, model=model)
        text = response.result if isinstance(response.result, str) else str(response.result)

        await self.memory.append(session_id, [{"role": "assistant", "content": text, "meta": {"agentId": self.id, "version": self.version}}])
        yield self.emit("final_result", session_id, payload={"message": text})


