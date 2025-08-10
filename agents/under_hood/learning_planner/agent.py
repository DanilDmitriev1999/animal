"""
// AICODE-NOTE: Минимальный агент-планировщик. Возвращает фиктивный план без LLM — для smoke-теста.
"""

from __future__ import annotations

import os

from ...base import AgentABC, Event
from ...registry import register_agent
from ...roles.policy import DialogueBuilder, to_openai_chat_messages
from ...registry import get_prompt
from ...memory import BackendMemory
from .so_schema import PlanSO, CreateTrackParams

# AICODE-NOTE: LLM прокидывается через фабрику/инициализацию, прямой импорт клиента не требуется



@register_agent("learning_planner", "v1")
def factory(memory, role_policy=None, meta=None, llm=None):
    # AICODE-NOTE: LLM прокидывается через фабрику и сохраняется в агенте
    return LearningPlannerAgent(memory=memory, role_policy=role_policy or {}, meta=meta or {}, llm=llm)


class LearningPlannerAgent(AgentABC):
    id = "learning_planner"
    version = "v1"

    def __init__(self, memory, role_policy=None, meta=None, llm=None):
        super().__init__(memory, role_policy=role_policy, meta=meta, llm=llm)

    async def _run(self, *, session_id: str, query: dict, **_):
        """Формирует учебный план.

        Принимает либо `user_message` (старый контракт: свободный текст), либо
        `params` из шага создания трека (см. фронт `/tracks/create`).
        Предпочтительно использовать `params`.
        """
        
        # planning
        yield self.emit("planning", session_id, payload={"message": "Формируем план курса"})

        # Подготовим текстовую тему из params или свободного сообщения
        create_params: CreateTrackParams | None = None

        create_params = CreateTrackParams(**query)


        topic_text = (
            f"Название: {create_params.title}.\n"
            f"Описание: {create_params.description}.\n"
            f"Цель: {create_params.goal}.\n"
            f"Тип обучения: {create_params.focus}. Тон: {create_params.tone}."
        )


        system_text = get_prompt("learning_planner.system")
        developer_text = get_prompt("learning_planner.developer").format(topic=topic_text)
        dialog = await DialogueBuilder.build(
            self.memory,
            session_id,
            self.role_policy,
            "planning",
            system_text=system_text,
            developer_text=developer_text,
        )

        # Минимальный LLM‑вызов
        model = self.meta.get("model") or os.getenv("AGENTS_DEFAULT_MODEL", "gpt-4.1-mini")
        messages = to_openai_chat_messages(dialog)


        response = await self.llm.structured_output(messages=messages, model=model, schema=PlanSO)


        plan = response.result

        result = {"plan": plan, "sources": []}
        await self.memory.append(session_id, [{"role": "assistant", "name": "planning", "content": result}])
        yield self.emit("final_result", session_id, payload=result)


