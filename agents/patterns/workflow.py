"""
// AICODE-NOTE: Скелеты workflow‑агентов: последовательный и циклический.
// AICODE-NOTE: Каждый step — это отдельный агент (наследник AgentABC) со своей LLM и архитектурой.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

from ..base import AgentABC, Event


class SequentialWorkflowAgentBase(AgentABC):
    """Выполняет набор шагов последовательно.

    steps: список кортежей (step_id, agent_instance).
    Каждый агент шага получает общий контекст `**ctx` и возвращает свой результат `dict`.
    Результаты шагов накапливаются в `history`.
    """

    id = "sequential_workflow_base"
    version = "v1"

    def __init__(self, memory, steps: list[tuple[str, AgentABC]], *, role_policy: dict | None = None, meta: dict | None = None):
        super().__init__(memory, role_policy=role_policy, meta=meta)
        self.steps = steps

    async def _run(self, *, session_id: str, **ctx) -> AsyncIterator[Event]:
        history: list[dict[str, Any]] = []
        for idx, (step_id, agent) in enumerate(self.steps, start=1):
            yield self.emit("workflow_step_start", session_id, payload={"step": idx, "id": step_id})
            # AICODE-NOTE: Каждый step — агент. Вызываем его run() и получаем финальный результат шага.
            result: Any = await agent.run(history=history, **ctx)
            item = {"step": idx, "id": step_id, "result": result}
            history.append(item)
            yield self.emit("workflow_step_done", session_id, payload=item)
        yield self.emit("final_result", session_id, payload={"history": history})


class LoopWorkflowAgentBase(AgentABC):
    """Выполняет цикл шагов, пока check_fn не вернёт done=True или не достигнут max_steps.

    plan_agent, act_agent, check_agent — агенты‑шаги, совместимые по контракту AgentABC.
    """

    id = "loop_workflow_base"
    version = "v1"

    def __init__(self, memory, plan_agent: AgentABC, act_agent: AgentABC, check_agent: AgentABC, *, max_steps: int = 10, role_policy: dict | None = None, meta: dict | None = None):
        super().__init__(memory, role_policy=role_policy, meta=meta)
        self.plan_agent = plan_agent
        self.act_agent = act_agent
        self.check_agent = check_agent
        self.max_steps = max_steps

    async def _run(self, *, session_id: str, **ctx) -> AsyncIterator[Event]:
        history: list[dict[str, Any]] = []
        for step in range(self.max_steps):
            yield self.emit("loop_step_start", session_id, payload={"step": step + 1})
            plan = await self.plan_agent.run(history=history, **ctx)
            act = await self.act_agent.run(plan=plan, history=history, **ctx)
            check = await self.check_agent.run(result=act, plan=plan, history=history, **ctx)
            item = {"step": step + 1, "plan": plan, "act": act, "check": check}
            history.append(item)
            yield self.emit("loop_step_done", session_id, payload=item)
            done = getattr(check, "done", False) or (isinstance(check, dict) and check.get("done"))
            if done:
                break
        yield self.emit("final_result", session_id, payload={"history": history})


__all__ = ["SequentialWorkflowAgentBase", "LoopWorkflowAgentBase"]


