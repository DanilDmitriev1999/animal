"""
// AICODE-NOTE: ReAct — класс‑скелет агента с циклом Decision→Action→Observation→Verdict.
"""

from __future__ import annotations

from typing import Any, Callable
from pydantic import BaseModel

from ..base import AgentABC


class Decision(BaseModel):
    thought: str
    action: str | None = None
    action_input: dict[str, Any] | None = None


class Observation(BaseModel):
    text: str


class Verdict(BaseModel):
    conclusion: str
    done: bool = False


class ReActAgentBase(AgentABC):
    """Базовый класс агента по паттерну ReAct.

    Ожидает async-колл `llm_call(prompt_id: str, **ctx) -> dict` и словарь `tools` с методами `run()`.
    Не стримит токены — только события шагов.
    """

    id = "react_base"
    version = "v1"

    def __init__(self, memory, llm_call: Callable[..., Any], tools: dict[str, Any] | None = None, *, role_policy: dict | None = None, max_steps: int = 5, meta: dict | None = None):
        super().__init__(memory, role_policy=role_policy, meta=meta)
        self.llm_call = llm_call
        self.tools = tools or {}
        self.max_steps = max_steps

    async def _run(self, *, session_id: str, **ctx):
        history: list[dict[str, Any]] = []
        yield self.emit("react_start", session_id, payload={})
        for step_idx in range(self.max_steps):
            yield self.emit("react_step_start", session_id, payload={"step": step_idx + 1})
            decided = await self.llm_call("react_decide", history=history, **ctx)
            decision = Decision.model_validate(decided)
            payload = {"decision": decision.model_dump()}
            if decision.action and decision.action in self.tools:
                obs = await self.tools[decision.action].run(**(decision.action_input or {}))
                observation = Observation(text=str(obs))
                payload["observation"] = observation.model_dump()
            history.append(payload)
            yield self.emit("react_step_done", session_id, payload=payload)
            verdict_raw = await self.llm_call("react_verdict", history=history, **ctx)
            verdict = Verdict.model_validate(verdict_raw)
            if verdict.done:
                history.append({"verdict": verdict.model_dump()})
                yield self.emit("final_result", session_id, payload={"history": history, "verdict": verdict.model_dump()})
                break


__all__ = ["Decision", "Observation", "Verdict", "ReActAgentBase"]


