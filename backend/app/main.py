"""
// AICODE-NOTE: FastAPI-приложение для фронтенда AI Learning.

- Совместимо с фронтом (`frontend/src/lib/api.ts`).
- Подключение к PostgreSQL через psycopg2 с ленивым пулом соединений.
- Эндпоинты:
  - GET /health
  - GET /tracks
  - GET /tracks/{slug}
  - GET /tracks/{slug}/roadmap
  - POST /sessions
  - GET /sessions/{sessionId}/messages/{tab}
  - POST /sessions/{sessionId}/messages/{tab}
- Задел для агентов: POST /run/agent/{id}/{version} (SSE-заглушка)

Переменные окружения БД: DB_URL или DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Dict, Iterable, List, Optional, AsyncIterator

from fastapi import FastAPI, HTTPException, Path, Body, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

# AICODE-NOTE: psycopg2 пул соединений и словарный курсор
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor


# ----------------------------------------------------------------------------
# Конфигурация
# ----------------------------------------------------------------------------


def build_db_url_from_env() -> str:
    db_url = os.getenv("DB_URL")
    if db_url:
        return db_url
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "user")
    password = os.getenv("DB_PASSWORD", "password")
    name = os.getenv("DB_NAME", "ai_learning_db")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


class AppState:
    db_pool: Optional[SimpleConnectionPool] = None


state = AppState()


def get_db_pool() -> SimpleConnectionPool:
    """Ленивая инициализация пула соединений к БД."""
    if state.db_pool is None:
        dsn = build_db_url_from_env()
        state.db_pool = SimpleConnectionPool(minconn=1, maxconn=8, dsn=dsn)
    return state.db_pool


class DB:
    """Примитивная обёртка для работы с БД (контекст курсора)."""

    def __init__(self) -> None:
        self._conn = None

    def __enter__(self):
        pool = get_db_pool()
        self._conn = pool.getconn()
        return self._conn

    def __exit__(self, exc_type, exc, tb):
        assert self._conn is not None
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            get_db_pool().putconn(self._conn)
            self._conn = None


# ----------------------------------------------------------------------------
# Pydantic-схемы
# ----------------------------------------------------------------------------


class TrackOut(BaseModel):
    id: str
    slug: str
    title: str
    description: Optional[str] = None
    goal: Optional[str] = None


class RoadmapItemOut(BaseModel):
    id: str
    position: int
    text: str
    done: bool


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    meta: Optional[Dict[str, Any]] = None


class CreateSessionIn(BaseModel):
    deviceId: str = Field(..., min_length=1)
    trackSlug: str = Field(..., min_length=1)


class CreateSessionOut(BaseModel):
    sessionId: str


class PostMessageIn(BaseModel):
    role: str
    content: str
    meta: Optional[Dict[str, Any]] = None


# ----------------------------------------------------------------------------
# Инициализация приложения
# ----------------------------------------------------------------------------


app = FastAPI(title="AI Learning API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


# ----------------------------------------------------------------------------
# Tracks
# ----------------------------------------------------------------------------


@app.get("/tracks", response_model=List[TrackOut])
def list_tracks() -> List[TrackOut]:
    with DB() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id::text AS id, slug, title, description, goal
                FROM tracks
                ORDER BY created_at ASC
                """
            )
            rows = cur.fetchall()
    return [TrackOut(**row) for row in rows]


@app.get("/tracks/{slug}", response_model=TrackOut)
def get_track(slug: str = Path(..., min_length=1)) -> TrackOut:
    with DB() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id::text AS id, slug, title, description, goal
                FROM tracks
                WHERE slug = %s
                """,
                (slug,),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Track not found")
    return TrackOut(**row)


@app.get("/tracks/{slug}/roadmap", response_model=List[RoadmapItemOut])
def get_track_roadmap(slug: str = Path(..., min_length=1)) -> List[RoadmapItemOut]:
    with DB() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT tri.id::text AS id, tri.position, tri.text, tri.done
                FROM track_roadmap_items tri
                JOIN tracks t ON t.id = tri.track_id
                WHERE t.slug = %s
                ORDER BY tri.position ASC
                """,
                (slug,),
            )
            rows = cur.fetchall()
    return [RoadmapItemOut(**row) for row in rows]


# ----------------------------------------------------------------------------
# Sessions
# ----------------------------------------------------------------------------


@app.post("/sessions", response_model=CreateSessionOut)
def create_or_get_session(payload: CreateSessionIn = Body(...)) -> CreateSessionOut:
    device_id = payload.deviceId
    track_slug = payload.trackSlug

    with DB() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # AICODE-NOTE: Upsert пользователя по device_id
            cur.execute(
                """
                INSERT INTO users (device_id) VALUES (%s)
                ON CONFLICT (device_id) DO UPDATE SET updated_at = now()
                RETURNING id::text AS id
                """,
                (device_id,),
            )
            user_id = cur.fetchone()["id"]

            # Найти трек
            cur.execute(
                """
                SELECT id::text AS id
                FROM tracks
                WHERE slug = %s
                """,
                (track_slug,),
            )
            row_track = cur.fetchone()
            if not row_track:
                raise HTTPException(status_code=404, detail="Track not found")
            track_id = row_track["id"]

            # Upsert сессии
            cur.execute(
                """
                INSERT INTO track_sessions (user_id, track_id)
                VALUES (%s::uuid, %s::uuid)
                ON CONFLICT (user_id, track_id)
                DO UPDATE SET updated_at = now()
                RETURNING id::text AS id
                """,
                (user_id, track_id),
            )
            session_id = cur.fetchone()["id"]

            # Обеспечить ветки чатов (chat|practice|simulation)
            for tab in ("chat", "practice", "simulation"):
                cur.execute(
                    """
                    INSERT INTO chat_threads (session_id, tab)
                    VALUES (%s::uuid, %s::chat_tab)
                    ON CONFLICT (session_id, tab) DO NOTHING
                    """,
                    (session_id, tab),
                )

    return CreateSessionOut(sessionId=session_id)


# ----------------------------------------------------------------------------
# Messages
# ----------------------------------------------------------------------------


def _get_thread_id_or_404(cur, session_id: str, tab: str) -> str:
    cur.execute(
        """
        SELECT id::text AS id
        FROM chat_threads
        WHERE session_id = %s::uuid AND tab = %s::chat_tab
        """,
        (session_id, tab),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Thread not found for session/tab")
    return row["id"]


@app.get("/sessions/{session_id}/messages/{tab}", response_model=List[MessageOut])
def list_messages(
    session_id: str = Path(..., description="Track session id (UUID as string)"),
    tab: str = Path(..., pattern="^(chat|practice|simulation)$"),
) -> List[MessageOut]:
    with DB() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            thread_id = _get_thread_id_or_404(cur, session_id, tab)
            cur.execute(
                """
                SELECT id::text AS id,
                       role::text AS role,
                       content,
                       to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') AS created_at,
                       meta_json AS meta
                FROM chat_messages
                WHERE thread_id = %s::uuid
                ORDER BY created_at ASC
                """,
                (thread_id,),
            )
            rows = cur.fetchall()
    # Pydantic конвертирует dict→модель
    return [MessageOut(**row) for row in rows]


@app.post("/sessions/{session_id}/messages/{tab}", response_model=MessageOut)
def post_message(
    session_id: str = Path(..., description="Track session id (UUID as string)"),
    tab: str = Path(..., pattern="^(chat|practice|simulation)$"),
    payload: PostMessageIn = Body(...),
) -> MessageOut:
    role = payload.role
    content = payload.content
    meta = payload.meta or {}

    with DB() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            thread_id = _get_thread_id_or_404(cur, session_id, tab)
            cur.execute(
                """
                INSERT INTO chat_messages (thread_id, role, content, meta_json)
                VALUES (%s::uuid, %s::message_role, %s, %s::jsonb)
                RETURNING id::text AS id,
                          role::text AS role,
                          content,
                          to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') AS created_at,
                          meta_json AS meta
                """,
                (thread_id, role, content, json.dumps(meta)),
            )
            row = cur.fetchone()

    return MessageOut(**row)


# ----------------------------------------------------------------------------
# Агент: JSON и SSE
# ----------------------------------------------------------------------------

try:
    # Подключаем пакет агентов, если доступен
    from agents import autodiscover, autodiscover_prompts
    from agents.registry import get_agent
    from agents.runner import run_agent_with_events
    from agents.memory.in_memory import InMemoryMemory
    from agents.memory.backend_memory import BackendMemory
    from agents.llm.base import LLMResponse
    from agents.llm.openai_llm import OpenAILLM
    _AGENTS_AVAILABLE = True
except Exception:  # pragma: no cover - пакет агентов может быть недоступен
    _AGENTS_AVAILABLE = False


@app.on_event("startup")
def _agents_autodiscover_startup() -> None:  # pragma: no cover - простая инициализация
    if _AGENTS_AVAILABLE:
        try:
            autodiscover()
            autodiscover_prompts()
        except Exception:
            pass


class RunPlannerIn(BaseModel):
    session_id: Optional[str] = None
    query: Dict[str, Any]
    memory: Optional[str] = Field(default="inmem", pattern="^(backend|inmem)$")


@app.post("/agents/learning_planner/v1/plan")
async def run_learning_planner_plan(body: RunPlannerIn) -> Dict[str, Any]:
    if not _AGENTS_AVAILABLE:
        raise HTTPException(status_code=501, detail="Agents package is not available")

    # Память
    if body.memory == "backend":
        memory = BackendMemory()
        session_id = body.session_id or "dev-session"
    else:
        memory = InMemoryMemory()
        session_id = body.session_id or "dev-session"

    # LLM: пытаемся создать реальный клиент, иначе — мок
    def _create_llm() -> Any:
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_BASE_URL"):
            try:
                return OpenAILLM()
            except Exception:
                pass

        class _StubLLM:
            def __init__(self, q: Dict[str, Any]):
                self.q = q

            async def structured_output(self, messages, *, schema, model=None, temperature=None):  # type: ignore[no-untyped-def]
                focus = str(self.q.get("focus", "theory"))
                modules: List[str] = [
                    "Вступление и постановка задачи",
                    "Ключевые понятия и термины",
                    "Глубокая теория с примерами" if focus == "theory" else "Практикум: первая мини‑задача",
                    "Типичные ошибки и как их избегать",
                    "Проект: применяем знания" if focus == "practice" else "Обзор дополнительных материалов",
                ]
                return LLMResponse(result={"modules": modules})

        return _StubLLM(body.query)

    llm = _create_llm()

    # Агент
    agent = get_agent("learning_planner", "v1", memory=memory, llm=llm)

    final_payload: Optional[Dict[str, Any]] = None
    async for ev in run_agent_with_events(agent, session_id=session_id, query=body.query):
        if ev.event == "final_result":
            final_payload = ev.payload or {}

    if not final_payload:
        raise HTTPException(status_code=500, detail="Agent did not produce a result")

    return final_payload


@app.post("/run/agent/{agent_id}/{version}")
async def run_agent_sse(
    request: Request,
    agent_id: str,
    version: str,
    memory: str = Query("inmem", pattern="^(backend|inmem)$"),
    body: Dict[str, Any] = Body(..., example={"session_id": "...", "query": {}}),
):
    if not _AGENTS_AVAILABLE:
        raise HTTPException(status_code=501, detail="Agents package is not available")

    # Память
    if memory == "backend":
        mem = BackendMemory()
        session_id = body.get("session_id") or "dev-session"
    else:
        mem = InMemoryMemory()
        session_id = body.get("session_id") or "dev-session"

    # LLM (реальный или мок)
    def _create_llm() -> Any:
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_BASE_URL"):
            try:
                return OpenAILLM()
            except Exception:
                pass

        class _StubLLM:
            def __init__(self, q: Dict[str, Any]):
                self.q = q

            async def structured_output(self, messages, *, schema, model=None, temperature=None):  # type: ignore[no-untyped-def]
                focus = str(self.q.get("focus", "theory"))
                modules: List[str] = [
                    "Вступление и постановка задачи",
                    "Ключевые понятия и термины",
                    "Глубокая теория с примерами" if focus == "theory" else "Практикум: первая мини‑задача",
                    "Типичные ошибки и как их избегать",
                    "Проект: применяем знания" if focus == "practice" else "Обзор дополнительных материалов",
                ]
                return LLMResponse(result={"modules": modules})

        return _StubLLM(body.get("query", {}))

    llm = _create_llm()

    agent = get_agent(agent_id, version, memory=mem, llm=llm)

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for ev in run_agent_with_events(agent, session_id=session_id, **{k: v for k, v in body.items() if k != "session_id"}):
                yield f"event: {ev.event}\n"
                yield "data: " + json.dumps({
                    "event": ev.event,
                    "session_id": ev.session_id,
                    "trace_id": ev.trace_id,
                    "payload": ev.payload or {},
                }) + "\n\n"
        except Exception as e:
            yield "event: error\n"
            yield "data: " + json.dumps({"event": "error", "payload": {"message": str(e)}}) + "\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ----------------------------------------------------------------------------
# Грейсфул-шатдаун пула БД
# ----------------------------------------------------------------------------


@app.on_event("shutdown")
def shutdown_event() -> None:
    if state.db_pool is not None:
        try:
            state.db_pool.closeall()
        finally:
            state.db_pool = None



