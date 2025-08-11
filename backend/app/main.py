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
import re
import logging
from urllib.parse import unquote
from typing import Any, Dict, Iterable, List, Optional, AsyncIterator

from fastapi import FastAPI, HTTPException, Path, Body, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse
from starlette.responses import JSONResponse

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

logger = logging.getLogger("ai_learning.api")


@app.middleware("http")
async def decoded_path_logger(request: Request, call_next):  # pragma: no cover - простое логирование
    try:
        path_decoded = unquote(str(request.url.path))
        logger.info("%s %s", request.method, path_decoded)
    except Exception:
        pass
    response = await call_next(request)
    return response


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


class CreateTrackIn(BaseModel):
    title: str
    description: Optional[str] = None
    goal: Optional[str] = None
    slug: Optional[str] = None
    roadmap: Optional[List[str]] = None


def _slugify_base(value: str) -> str:
    base = value.strip().lower()
    base = re.sub(r"\s+", "-", base)
    base = re.sub(r"[^\w\-]", "", base)
    base = re.sub(r"-+", "-", base).strip("-")
    return base or "track"


@app.post("/tracks", response_model=TrackOut)
def create_track(body: CreateTrackIn) -> TrackOut:
    title = body.title
    description = body.description or None
    goal = body.goal or None
    desired_slug = body.slug or _slugify_base(title)
    roadmap = [t for t in (body.roadmap or []) if isinstance(t, str) and t.strip()]

    with DB() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Подбираем уникальный slug
            slug = desired_slug
            suffix = 2
            while True:
                cur.execute("SELECT 1 FROM tracks WHERE slug = %s", (slug,))
                if cur.fetchone() is None:
                    break
                slug = f"{desired_slug}-{suffix}"
                suffix += 1

            # Вставка трека
            cur.execute(
                """
                INSERT INTO tracks (slug, title, description, goal)
                VALUES (%s, %s, %s, %s)
                RETURNING id::text AS id, slug, title, description, goal
                """,
                (slug, title, description, goal),
            )
            row = cur.fetchone()
            track_id = row["id"]

            # Вставка роадмапа
            position = 1
            for text in roadmap:
                cur.execute(
                    """
                    INSERT INTO track_roadmap_items (track_id, position, text, done)
                    VALUES (%s::uuid, %s, %s, false)
                    """,
                    (track_id, position, text.strip()),
                )
                position += 1

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
# Synopsis (live + versions)
# ----------------------------------------------------------------------------


class SynopsisIn(BaseModel):
    title: str
    items: List[Dict[str, Any]]


class SynopsisOut(BaseModel):
    title: str
    items: List[Dict[str, Any]]
    lastUpdated: Optional[str] = None


@app.get("/sessions/{session_id}/synopsis", response_model=SynopsisOut)
def get_synopsis(session_id: str = Path(...)) -> SynopsisOut:
    with DB() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT s.title,
                       sv.items_json AS items,
                       to_char(sv.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') AS last_updated
                FROM synopses s
                JOIN synopsis_versions sv ON sv.id = s.current_version_id
                WHERE s.session_id = %s::uuid
                """,
                (session_id,),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Synopsis not found")
    return SynopsisOut(title=row["title"], items=row["items"], lastUpdated=row["last_updated"])  # type: ignore[index]


@app.post("/sessions/{session_id}/synopsis", response_model=SynopsisOut)
def upsert_synopsis(session_id: str, body: SynopsisIn) -> SynopsisOut:
    with DB() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Ensure container
            cur.execute("SELECT id::text AS id FROM synopses WHERE session_id = %s::uuid", (session_id,))
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    """
                    INSERT INTO synopses (session_id, title)
                    VALUES (%s::uuid, %s)
                    RETURNING id::text AS id
                    """,
                    (session_id, body.title),
                )
                syn_id = cur.fetchone()["id"]
            else:
                syn_id = row["id"]

            # New version number
            cur.execute("SELECT COALESCE(MAX(version_num), 0) + 1 AS v FROM synopsis_versions WHERE synopsis_id = %s::uuid", (syn_id,))
            v = cur.fetchone()["v"]

            # Insert version
            cur.execute(
                """
                INSERT INTO synopsis_versions (synopsis_id, version_num, items_json, kind)
                VALUES (%s::uuid, %s, %s::jsonb, 'generated')
                RETURNING id::text AS id, to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') AS created
                """,
                (syn_id, v, json.dumps(body.items)),
            )
            version_row = cur.fetchone()

            # Update pointer
            cur.execute(
                """
                UPDATE synopses SET title = %s, current_version_id = %s::uuid, updated_at = now()
                WHERE id = %s::uuid
                """,
                (body.title, version_row["id"], syn_id),
            )

            return SynopsisOut(title=body.title, items=body.items, lastUpdated=version_row["created"])  # type: ignore[index]


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

try:
    # AICODE-NOTE: Очередь фоновых заданий (Redis/RQ)
    from backend.worker.queue import get_redis_and_queue
    from backend.worker.tasks import run_agent_job
    _JOBS_AVAILABLE = True
except Exception:
    _JOBS_AVAILABLE = False


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

    llm = OpenAILLM()

    # Агент
    agent = get_agent("learning_planner", "v1", memory=memory, llm=llm)

    final_payload: Optional[Dict[str, Any]] = None
    async for ev in run_agent_with_events(agent, session_id=session_id, query=body.query):
        if ev.event == "final_result":
            final_payload = ev.payload or {}

    if not final_payload:
        raise HTTPException(status_code=500, detail="Agent did not produce a result")

    return final_payload


class RunSynopsisIn(BaseModel):
    session_id: Optional[str] = None
    query: Dict[str, Any]
    memory: Optional[str] = Field(default="inmem", pattern="^(backend|inmem)$")


@app.post("/agents/synopsis_manager/v1/synopsis")
async def run_synopsis_manager_synopsis(
    body: RunSynopsisIn,
    mode: str = Query("sync", pattern="^(background|sync)$"),
) -> Dict[str, Any]:
    if not _AGENTS_AVAILABLE:
        raise HTTPException(status_code=501, detail="Agents package is not available")

    # AICODE-NOTE: background режим — кладём задачу в очередь и сразу возвращаем 202 + jobId
    if mode == "background":
        if not _JOBS_AVAILABLE:
            raise HTTPException(status_code=501, detail="Jobs/worker is not available")
        try:
            _, rq_queue = get_redis_and_queue()
            from os import getenv
            job_timeout = int(getenv("AGENT_JOB_TIMEOUT", "900"))
            result_ttl = int(getenv("AGENT_RESULT_TTL", "600"))
            job = rq_queue.enqueue(
                run_agent_job,
                {
                    "agent_id": "synopsis_manager",
                    "version": "v1",
                    "session_id": body.session_id,
                    "memory": body.memory or "inmem",
                    "query": body.query,
                    "apply_side_effects": True,
                },
                job_timeout=job_timeout,
                result_ttl=result_ttl,
            )
            return JSONResponse(status_code=202, content={"jobId": job.id})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to enqueue job: {e}")

    # Память
    if body.memory == "backend":
        memory = BackendMemory()
        session_id = body.session_id or "dev-session"
    else:
        memory = InMemoryMemory()
        session_id = body.session_id or "dev-session"


    llm = OpenAILLM()

    agent = get_agent("synopsis_manager", "v1", memory=memory, llm=llm)

    final_payload: Optional[Dict[str, Any]] = None
    async for ev in run_agent_with_events(agent, session_id=session_id, query=body.query):
        if ev.event == "final_result":
            final_payload = ev.payload or {}

    if not final_payload:
        raise HTTPException(status_code=500, detail="Agent did not produce a result")

    # AICODE-NOTE: Сохраняем live‑конспект в БД (версионная схема)
    synopsis = (final_payload or {}).get("synopsis") or {}
    title = str(((body.query.get("params") or body.query).get("title")) or "Конспект")
    items = synopsis.get("items", [])
    with DB() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Проверим, что сессия существует (иначе могли использовать inmem)
            cur.execute(
                """
                SELECT ts.id::text AS id
                FROM track_sessions ts
                WHERE ts.id = %s::uuid
                """,
                (session_id,),
            )
            if cur.fetchone() is None:
                return final_payload

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

    llm = OpenAILLM()

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
# Jobs API: enqueue + status (Redis/RQ, без таблицы в БД)
# ----------------------------------------------------------------------------


class EnqueueAgentJobIn(BaseModel):
    session_id: Optional[str] = None
    memory: Optional[str] = Field(default="inmem", pattern="^(backend|inmem)$")
    query: Dict[str, Any]
    apply_side_effects: Optional[bool] = True


class EnqueueAgentJobOut(BaseModel):
    jobId: str


@app.post("/jobs/agents/{agent_id}/{version}", response_model=EnqueueAgentJobOut, status_code=202)
def enqueue_agent_job(agent_id: str, version: str, body: EnqueueAgentJobIn) -> EnqueueAgentJobOut:
    if not _JOBS_AVAILABLE:
        raise HTTPException(status_code=501, detail="Jobs/worker is not available")
    try:
        _, rq_queue = get_redis_and_queue()
        from os import getenv
        job_timeout = int(getenv("AGENT_JOB_TIMEOUT", "900"))
        result_ttl = int(getenv("AGENT_RESULT_TTL", "600"))
        job = rq_queue.enqueue(
            run_agent_job,
            {
                "agent_id": agent_id,
                "version": version,
                "session_id": body.session_id,
                "memory": body.memory or "inmem",
                "query": body.query,
                "apply_side_effects": bool(body.apply_side_effects) if body.apply_side_effects is not None else True,
            },
            job_timeout=job_timeout,
            result_ttl=result_ttl,
        )
        return EnqueueAgentJobOut(jobId=job.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enqueue job: {e}")


class JobStatusOut(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/jobs/{job_id}", response_model=JobStatusOut)
def get_job_status(job_id: str) -> JobStatusOut:
    if not _JOBS_AVAILABLE:
        raise HTTPException(status_code=501, detail="Jobs/worker is not available")
    try:
        from rq.job import Job  # type: ignore
        redis, _ = get_redis_and_queue()
        job = Job.fetch(job_id, connection=redis)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    raw = job.get_status() or "queued"
    # AICODE-NOTE: Нормализуем статус к контракту API
    if raw in {"queued", "scheduled", "deferred"}:
        status = "queued"
    elif raw in {"started"}:
        status = "running"
    elif raw in {"finished"}:
        status = "done"
    elif raw in {"failed", "stopped", "canceled"}:
        status = "failed"
    else:
        status = raw

    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    if status == "done":
        try:
            result = job.result if isinstance(job.result, dict) else None
        except Exception:
            result = None
    if status == "failed":
        try:
            error = (job.exc_info or "").splitlines()[-1] if job.exc_info else "Job failed"
        except Exception:
            error = "Job failed"

    return JobStatusOut(status=status, result=result, error=error)


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



