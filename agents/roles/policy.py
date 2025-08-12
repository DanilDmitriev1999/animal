"""
// AICODE-NOTE: Политики ролей и сборщик диалога.
"""

from __future__ import annotations

from pydantic import BaseModel


class RolePolicy(BaseModel):
    provider_mode: str = "assistant-only"
    synthetic_user_between_steps: bool = False
    inject_system: bool = True
    assistant_name_by_step: bool = True


class DialogueBuilder:
    @staticmethod
    async def build(memory, session_id: str, role_policy: dict, step_name: str, system_text: str, developer_text: str):
        messages: list[dict] = []
        if role_policy.get("inject_system", True):
            messages.append({"role": "system", "content": system_text})
        # Историю сообщений загружаем ПЕРЕД текущим запросом, чтобы LLM учитывал контекст,
        # а затем добавляем текущий user-запрос последним.
        prior = await memory.load_dialog(session_id, role_policy)
        messages.extend(prior)
        messages.append({"role": "user", "content": developer_text})
        if role_policy.get("synthetic_user_between_steps", False):
            messages.append({"role": "user", "content": f"continue:{step_name}"})
        return messages


def to_openai_chat_messages(messages: list[dict]) -> list[dict]:
    """Преобразовать внутренние сообщения в формат OpenAI Chat Completions.

    - Роль `developer` маппится в `system` (инструкции подсистемы).
    - Неизвестные роли по умолчанию маппятся в `user`.
    - Доп. поля (например, name) сохраняются при наличии.
    """

    allowed = {"system", "user", "assistant"}
    converted: list[dict] = []
    for m in messages:
        role = m.get("role", "user")
        if role == "developer":
            role = "system"
        if role not in allowed:
            role = "user"
        out = {"role": role, "content": m.get("content", "")}
        if "name" in m and isinstance(m["name"], str) and m["name"]:
            out["name"] = m["name"]
        converted.append(out)
    return converted


__all__ = ["RolePolicy", "DialogueBuilder", "to_openai_chat_messages"]


