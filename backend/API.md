# API взаимодействие с БД

// AICODE-NOTE: Документирует REST API поверх PostgreSQL. Реализация в `backend/app/main.py`.

- Реализация: `backend/app/main.py`
- Зависимости: `backend/requirements.txt`
- Схема БД: `backend/sql/01_schema.sql` (+ сиды `backend/sql/02_seed.sql`)
- Запуск: `make api` → `http://localhost:8000`

## Общие
- БД: PostgreSQL (см. `docker-compose.yml`)
- Драйвер: `psycopg2`
- Формат ответов: JSON
- CORS: `http://localhost:3000`, `http://127.0.0.1:3000`
- Аутентификация: временно нет; используется `deviceId` (гость)

## Базовый URL
```
http://localhost:8000
```

## Эндпоинты

### Health
- `GET /health` → `{ "status": "ok" }`

### Tracks
- Функции: `list_tracks`, `get_track`, `get_track_roadmap` (см. `backend/app/main.py`)
- Таблицы: `tracks`, `track_roadmap_items`

1) Список треков
- `GET /tracks`
- Ответ `[Track]`
```
Track { id: string, slug: string, title: string, description?: string, goal?: string }
```

2) Трек по `slug`
- `GET /tracks/{slug}` → `Track`
- `404` если не найден

3) Roadmap трека
- `GET /tracks/{slug}/roadmap` → `[RoadmapItem]`
```
RoadmapItem { id: string, position: number, text: string, done: boolean }
```

### Sessions
- Функция: `create_or_get_session` (см. `backend/app/main.py`)
- Таблицы: `users`, `track_sessions`, `chat_threads`

1) Создать/получить сессию
- `POST /sessions`
- Тело:
```
{ "deviceId": string, "trackSlug": string }
```
- Ответ: `{ "sessionId": string }`
- Побочные эффекты:
  - upsert `users` по `device_id`
  - upsert `track_sessions` по `(user_id, track_id)`
  - создаются ветки `chat_threads` для `chat|practice|simulation`

### Messages
- Функции: `list_messages`, `post_message` (см. `backend/app/main.py`)
- Таблицы: `chat_threads`, `chat_messages`

1) Список сообщений ветки
- `GET /sessions/{sessionId}/messages/{tab}` (`tab ∈ chat|practice|simulation`)
- Ответ `[Message]`:
```
Message { id: string, role: "user"|"assistant"|"tool", content: string, created_at: string, meta?: object }
```

2) Добавить сообщение
- `POST /sessions/{sessionId}/messages/{tab}`
- Тело:
```
{ "role": "user"|"assistant"|"tool", "content": string, "meta"?: object }
```
- Ответ: `Message`
- `404` если ветка не найдена (не создана сессия)

## Маппинг API → SQL
- `/tracks` → `SELECT ... FROM tracks`
- `/tracks/{slug}` → `SELECT ... WHERE slug=$1`
- `/tracks/{slug}/roadmap` → `JOIN tracks ↔ track_roadmap_items`
- `POST /sessions` → upsert `users`, upsert `track_sessions`, ensure `chat_threads`
- `GET/POST /sessions/{id}/messages/{tab}` → `JOIN chat_threads` и `INSERT chat_messages`

### Synopsis (live + versions)
- Таблицы: `synopses`, `synopsis_versions`
- `GET /sessions/{sessionId}/synopsis` → текущая live‑версия: `{ title, items, lastUpdated }`
- `POST /sessions/{sessionId}/synopsis` → создаёт новую версию и назначает её текущей

#### Фоновая генерация конспекта через агента

- JSON: `POST /agents/synopsis_manager/v1/synopsis?mode=background|sync`
  - По умолчанию `mode=sync` (синхронная работа, как раньше). При `mode=background` — задание ставится в очередь Redis/RQ и возвращается `202 { jobId }`.
  - Тело и результат те же, что и для синхронного вызова.
  - Побочный эффект при завершении фонового задания: новая live‑версия сохраняется в БД, как и при sync‑режиме.

## Контракты
- `users.device_id` уникален; 1 сессия на пару `(user_id, track_id)`.
- Для сессии всегда есть ветки `chat|practice|simulation`.
- Порядок сообщений — по возрастанию `created_at`.

## Расширение (рекомендации)
- `/sessions/{id}/synopses` — CRUD по конспектам (`synopses`).
- `/templates` — выдача LLM-шаблонов (`chat_templates`).
- `/tracks` (POST/PATCH) — создание трека и управление роадмапом.

## Примеры
```
# список треков
curl http://localhost:8000/tracks | jq

# создать/получить сессию
echo '{"deviceId":"dev-device","trackSlug":"product-manager-ai-products"}' \
| curl -sX POST http://localhost:8000/sessions -H 'Content-Type: application/json' -d @- | jq

# отправить сообщение в чат
echo '{"role":"user","content":"Привет!"}' \
| curl -sX POST http://localhost:8000/sessions/<SESSION_ID>/messages/chat -H 'Content-Type: application/json' -d @- | jq
```


## Взаимодействие с фронтендом

// AICODE-NOTE: Этот раздел описывает, какие файлы фронтенда обращаются к каким эндпоинтам.

- Клиентская обёртка над REST API: `frontend/src/lib/api.ts`
  - Базовый URL задаётся через `NEXT_PUBLIC_API_URL` (например, `http://localhost:8000`).
  - Методы: `getTracks`, `getTrack`, `getRoadmap`, `createOrGetSession`, `getMessages`, `postMessage`.
- Идентификатор пользователя (в отсутствие авторизации): `frontend/src/lib/device.ts`
  - Возвращает фиксированный ID `dev-device` или `process.env.NEXT_PUBLIC_FIXED_DEVICE_ID`.

### Страницы
- Список треков: `frontend/src/app/tracks/page.tsx`
  - on mount → `api.getTracks()` → рендер карточек треков.

- Страница трека: `frontend/src/app/tracks/[slug]/page.tsx`
  - Распаковка параметров: `const { slug } = React.use(params)`.
  - Параллельно запрашивает:
    - `api.getTrack(slug)` → заголовок/описание/цель.
    - `api.createOrGetSession(deviceId, slug)` → `sessionId` (создаёт ветки чатов).
    - `api.getRoadmap(slug)` → передаётся в `TrackSidebar` как `roadmap`.
    - `api.getMessages(sessionId, tab)` для `chat|practice|simulation` → список сообщений.
  - Отправка сообщения: `ChatComposer` вызывает `api.postMessage(sessionId, activeTab, { role:'user', content })` и оптимистично добавляет сообщение в локальный стейт.
  - На экране есть фиксированный приветственный `ChatMessage` от ИИ; он не отправляется в API.

---

## Агенты: как добавлять в API

// AICODE-NOTE: Бэкенд уже содержит базовую интеграцию пакета `agents` и два способа вызова:
- JSON‑маршрут под конкретный агент (пример — планировщик)
- Универсальный SSE‑маршрут

### Готовые маршруты
- JSON: `POST /agents/learning_planner/v1/plan`
  - Тело:
    ```json
    { "session_id": "optional", "memory": "backend|inmem", "query": { "title": "...", "description": "...", "goal": "...", "focus": "theory|practice", "tone": "strict|friendly|motivational|neutral" } }
    ```
  - Ответ: `{ "plan": { "modules": string[] }, "sources": [] }`

- JSON: `POST /agents/synopsis_manager/v1/synopsis`
  - Тело:
  ```json
  {
    "session_id": "optional",
    "memory": "backend|inmem",
    "query": {
      "action": "create|update",
      "params": {
        "title": "...",
        "description": "...",
        "goal": "...",
        "focus": "theory|practice",
        "tone": "strict|friendly|motivational|neutral"
      },
      "plan": ["Модуль 1", "Модуль 2"],
      "synopsis": [ /* опционально, текущая версия */ ],
      "instructions": "опционально: свободные правки"
    }
  }
  ```
  - Ответ (sync): `{ "synopsis": { "items": [...], "lastUpdated": "YYYY-MM-DD HH:MM" }, "sources": [] }`
  - Ответ (background): `202 { "jobId": "..." }`
  - Побочный эффект: сохранение новой live‑версии в БД (`synopses/synopsis_versions`).

- SSE (универсальный): `POST /run/agent/{id}/{version}?memory=backend|inmem`
  - Тело: произвольный объект контекста (например, `{ "session_id": "...", "query": { ... } }`)
  - Ответ: поток событий `text/event-stream` (`start_agent`, `planning`, `final_result`, `error`).

Примеры curl:
```bash
# JSON‑вызов планировщика
curl -sX POST http://localhost:8000/agents/learning_planner/v1/plan \
  -H 'Content-Type: application/json' \
  -d '{"query":{"title":"Intro","description":"...","goal":"...","focus":"theory","tone":"friendly"}}' | jq

# SSE‑вызов любого агента
curl -N -sX POST 'http://localhost:8000/run/agent/learning_planner/v1?memory=inmem' \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"dev-s1","query":{"title":"Intro","description":"...","goal":"...","focus":"practice","tone":"neutral"}}'

# JSON‑вызов менеджера конспекта
curl -sX POST http://localhost:8000/agents/synopsis_manager/v1/synopsis \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id": "dev-s1",
    "memory": "inmem",
    "query": {
      "action": "create",
      "params": { "title": "Введение в нейросети", "description": "...", "goal": "...", "focus": "theory", "tone": "friendly" },
      "plan": ["Введение", "Ключевые понятия", "Практика"]
    }
  }'
```

### Разговорные агенты (JSON)
- `POST /agents/mentor_chat/v1/reply`
  - Тело:
  ```json
  { "session_id": "optional", "memory": "backend|inmem", "user_message": "строка", "apply_side_effects": true }
  ```
  - Ответ: `{ "message": "текст ответа" }`
  - Побочный эффект при `apply_side_effects=true` и наличии `session_id`: сообщение ассистента пишется в ветку `chat` той же сессии.

- `POST /agents/practice_coach/v1/hint`
  - Тело/ответ аналогичны; запись в ветку `practice`.

- `POST /agents/simulation_mentor/v1/turn`
  - Тело/ответ аналогичны; запись в ветку `simulation`.

Примеры:
```bash
curl -sX POST http://localhost:8000/agents/mentor_chat/v1/reply \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"dev-s1","memory":"inmem","user_message":"Привет!"}' | jq

curl -sX POST http://localhost:8000/agents/practice_coach/v1/hint \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"dev-s1","memory":"inmem","user_message":"Дай первый шаг"}' | jq

curl -sX POST http://localhost:8000/agents/simulation_mentor/v1/turn \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"dev-s1","memory":"inmem","user_message":"Смоделируй разговор"}' | jq
```
### Как добавить нового агента (пошагово)
1) Определите агента в пакете `agents`:
   - Файл: `agents/under_hood/<agent_id>/agent.py`
   - Фабрика: `@register_agent("<agent_id>", "v1")`
   - Метод: `async def _run(self, *, session_id: str, query: dict, **ctx)` → обязан эмитить `final_result` с полезной нагрузкой.
   - Промпты положите рядом (`prompts.yaml`, `prompts_developer.yaml`).

2) Бэкенд подхватит агента автоматически:
   - При старте вызывается `autodiscover()` и `autodiscover_prompts()`.

3) Выберите способ экспонировать в API:
   - Быстро сразу: используйте универсальный SSE‑маршрут `POST /run/agent/{id}/{version}` (ничего добавлять в API не нужно).
    - Удобный JSON‑обёртчик (sync/async): добавьте тонкий маршрут в `backend/app/main.py`, который:
     - описывает `pydantic`‑вход, собирает `memory=BackendMemory|InMemoryMemory`, создаёт LLM (реальный `OpenAILLM` или мок),
      - запускает `run_agent_with_events(agent, session_id=..., **payload)` и возвращает `payload` из события `final_result` (sync),
      - или ставит задачу в Redis/RQ и возвращает `202 { jobId }` (background).

Минимальный контракт JSON‑обёртки:
```json
// request
{ "session_id": "optional", "memory": "backend|inmem", "query": { /* вход для агента */ } }

// response
{ "...": "полезная нагрузка финального события агента" }
```

### Замечания
- `memory=backend` требует доступности текущего REST API (сам себя дергает по HTTP). Для локального режима подойдёт `inmem`.
- Если нет `OPENAI_API_KEY`/`OPENAI_BASE_URL`, бэкенд использует мок‑LLM (детерминированный черновик).
- Все события и трейсинг абстрагированы в пакете `agents` (см. `agents/AGENT.md`).

### Компоненты
- Поле ввода/кнопка отправки: `frontend/src/components/ChatComposer/index.tsx`.
- Сообщения: `frontend/src/components/ui/ChatMessage.tsx`.
- Сайдбар трека (описание/цель/roadmap): `frontend/src/components/TrackSidebar/index.tsx`.

### Ожидаемая конфигурация окружения для фронта
Создать `frontend/.env.local` (пример):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIXED_DEVICE_ID=dev-device
```

### Пользовательский поток
1. Пользователь открывает `/tracks` → фронт вызывает `GET /tracks` и показывает карточку сид‑трека.
2. Переходит по карточке → `/tracks/{slug}`:
   - фронт запрашивает `GET /tracks/{slug}`, `GET /tracks/{slug}/roadmap`, `POST /sessions` (по фиксированному deviceId), затем `GET /sessions/{id}/messages/{tab}` для всех трёх табов.
3. Пользователь пишет сообщение в любую вкладку → фронт отправляет `POST /sessions/{id}/messages/{tab}` и сразу добавляет его в UI.
4. Генерация конспекта: фронт может вызвать `POST /agents/synopsis_manager/v1/synopsis?mode=background` → получит `jobId` и начнёт поллинг `GET /jobs/{jobId}` или сразу `GET /sessions/{sessionId}/synopsis`.

### Jobs API (Redis/RQ, без таблицы в БД)

- `POST /jobs/agents/{id}/{version}` → 202 `{ jobId }` — поставить выполнение агента в очередь
- `GET /jobs/{jobId}` → `{ status: queued|running|done|failed, result?, error? }`

Пример enqueue + статус:
```bash
curl -sX POST http://localhost:8000/jobs/agents/synopsis_manager/v1 \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id": "dev-s1",
    "memory": "inmem",
    "query": { "action": "create", "params": { "title": "Intro", "description": "...", "goal": "...", "focus": "theory", "tone": "friendly" }, "plan": ["Введение"] }
  }' | jq

curl -s http://localhost:8000/jobs/<JOB_ID> | jq
```


