"""
// AICODE-NOTE: Общий раннер агента: управляет событиями и трейсингом.
"""

from __future__ import annotations

from typing import AsyncIterator

from .base import Event
from .callbacks import callbacks
from .tracing import Trace


async def run_agent_with_events(agent, /, **payload) -> AsyncIterator[Event]:
    # AICODE-NOTE: Сохраняем информацию о типе LLM и модели в payload трейса (без сериализации объекта LLM)
    llm_type = type(getattr(agent, "llm", None)).__name__ if getattr(agent, "llm", None) is not None else None
    model_name = None
    try:
        model_name = (getattr(agent, "meta", {}) or {}).get("model")
    except Exception:
        model_name = None
    trace_payload = {**payload, "llm_type": llm_type, "model": model_name}
    trace = Trace.start(
        entity_type="agent",
        entity_id=getattr(agent, "id", "unknown"),
        version=getattr(agent, "version", "unknown"),
        payload=trace_payload,
    )
    try:
        callbacks.fire("before", "agent", trace=trace, agent=agent, payload=payload)
        async for ev in agent.run_with_events(**payload):
            # Сохраняем событие в трейс и отдаём наружу
            Trace.event(trace, ev)
            yield ev
        callbacks.fire("after", "agent", trace=trace, agent=agent, payload=payload)
        Trace.finish(trace, status="success")
    except Exception as e:  # pragma: no cover - ошибки пробрасываем, но формируем событие
        err = Event(event="error", session_id=payload.get("session_id", ""), trace_id=str(trace.id), payload={"message": str(e)})
        Trace.event(trace, err)
        Trace.finish(trace, status="error")
        yield err


__all__ = ["run_agent_with_events"]


