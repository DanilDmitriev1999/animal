from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional

from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

# AICODE-NOTE: Импорт агентов
from agents import autodiscover, autodiscover_prompts  # type: ignore
from agents.registry import get_agent  # type: ignore
from agents.runner import run_agent_with_events  # type: ignore
from agents.memory.in_memory import InMemoryMemory  # type: ignore
from agents.memory.backend_memory import BackendMemory  # type: ignore
from agents.llm.openai_llm import OpenAILLM  # type: ignore


class AgentJobPayload(BaseModel):
    agent_id: str
    version: str
    session_id: Optional[str] = None
    memory: str = "inmem"  # "backend" | "inmem"
    query: Dict[str, Any]
    # AICODE-NOTE: Управление доменными побочными эффектами (например, запись live‑конспекта)
    apply_side_effects: bool = True


def _build_memory(kind: str):
    if kind == "backend":
        return BackendMemory()
    return InMemoryMemory()


def _ensure_agents_loaded() -> None:
    try:
        autodiscover()
        autodiscover_prompts()
    except Exception:
        pass


def run_agent_job(payload_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    // AICODE-NOTE: Синхронная задача RQ.
    Запускает агента, дожидается `final_result`, при необходимости применяет доменные побочные эффекты
    (например, запись live‑конспекта в БД), и возвращает итоговый payload.
    """
    payload = AgentJobPayload.model_validate(payload_dict)

    _ensure_agents_loaded()
    memory = _build_memory(payload.memory)
    session_id = payload.session_id or "dev-session"
    llm = OpenAILLM()

    agent = get_agent(payload.agent_id, payload.version, memory=memory, llm=llm)

    final_payload: Dict[str, Any] | None = None

    async def _run() -> Dict[str, Any]:
        nonlocal final_payload
        async for ev in run_agent_with_events(agent, session_id=session_id, query=payload.query):
            if ev.event == "final_result":
                final_payload = ev.payload or {}
        if final_payload is None:
            return {}
        return final_payload

    final_payload = asyncio.run(_run())

    # Доменные побочные эффекты (пример — live‑конспект)
    if payload.apply_side_effects and payload.agent_id == "synopsis_manager" and final_payload:
        try:
            synopsis = (final_payload or {}).get("synopsis") or {}
            title = str(((payload.query.get("params") or payload.query).get("title")) or "Конспект")
            items = synopsis.get("items", [])
            # AICODE-NOTE: прямое сохранение в БД по схеме API (без импорта эндпоинта)
            conn = psycopg2.connect(dsn=_build_db_url_from_env())
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Проверим, что сессия существует
                    cur.execute(
                        """
                        SELECT ts.id::text AS id
                        FROM track_sessions ts
                        WHERE ts.id = %s::uuid
                        """,
                        (session_id,),
                    )
                    if cur.fetchone() is None:
                        conn.rollback()
                        return final_payload or {}

                    # Контейнер синопсиса
                    cur.execute("SELECT id::text AS id FROM synopses WHERE session_id = %s::uuid", (session_id,))
                    row = cur.fetchone()
                    if row is None:
                        cur.execute(
                            """
                            INSERT INTO synopses (session_id, title)
                            VALUES (%s::uuid, %s)
                            RETURNING id::text AS id
                            """,
                            (session_id, title),
                        )
                        syn_id = cur.fetchone()["id"]
                    else:
                        syn_id = row["id"]

                    # Следующий номер версии
                    cur.execute(
                        "SELECT COALESCE(MAX(version_num), 0) + 1 AS v FROM synopsis_versions WHERE synopsis_id = %s::uuid",
                        (syn_id,),
                    )
                    v = cur.fetchone()["v"]

                    # Новая версия и перенос указателя current_version_id
                    cur.execute(
                        """
                        INSERT INTO synopsis_versions (synopsis_id, version_num, items_json, kind)
                        VALUES (%s::uuid, %s, %s::jsonb, 'generated')
                        RETURNING id::text AS id
                        """,
                        (syn_id, v, json.dumps(items)),
                    )
                    ver_id = cur.fetchone()["id"]
                    cur.execute(
                        "UPDATE synopses SET title = %s, current_version_id = %s::uuid, updated_at = now() WHERE id = %s::uuid",
                        (title, ver_id, syn_id),
                    )
                    conn.commit()
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
        except Exception:
            # AICODE-NOTE: побочный эффект не должен падать всю задачу
            pass

    return final_payload or {}


def _build_db_url_from_env() -> str:
    db_url = os.getenv("DB_URL")
    if db_url:
        return db_url
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "user")
    password = os.getenv("DB_PASSWORD", "password")
    name = os.getenv("DB_NAME", "ai_learning_db")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


