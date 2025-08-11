## Воркер агентов (Redis/RQ)

Документ описывает устройство фонового воркера, ключи в Redis, жизненный цикл заданий и практику эксплуатации/расширения.

// AICODE-NOTE: Статусы задач и результаты хранятся только в Redis (TTL). Доменные артефакты (например, live‑конспект) пишутся в PostgreSQL по завершении задачи.

### Быстрый старт

- Переменные окружения (см. `env.example`):
  - `REDIS_URL` — адрес Redis, например `redis://localhost:6379/0`
  - `AGENT_QUEUE` — имя очереди, по умолчанию `agents`
  - `AGENT_JOB_TIMEOUT` — таймаут выполнения задачи (сек), по умолчанию `900`
  - `AGENT_RESULT_TTL` — TTL хранения результата в Redis (сек), по умолчанию `600`
  - `AGENT_WORKER_SIMPLE` — `1` включает SimpleWorker (без форков, удобно на macOS)
  - `AGENT_WORKER_LOG_LEVEL` — уровень логгирования воркера (`INFO` по умолчанию)

- Запуск:
  - API: `make api`
  - Воркер: `make worker` (по умолчанию SimpleWorker, без форков)

- Проверка:
  - Поставить задачу: `POST /jobs/agents/synopsis_manager/v1` → `202 { jobId }`
  - Статус: `GET /jobs/{jobId}` → `{ status, result?, error? }`
  - Альтернатива: `POST /agents/synopsis_manager/v1/synopsis?mode=background` → `202 { jobId }`

## Архитектура и поток выполнения

### Модули

- `backend/worker/queue.py` — инициализация Redis и очереди RQ (`get_redis_and_queue`) на основе `REDIS_URL` и `AGENT_QUEUE`.
- `backend/worker/tasks.py` — универсальная задача `run_agent_job(payload)`:
  - загружает регистрацию агентов (`autodiscover`),
  - создает память (`BackendMemory|InMemoryMemory`), LLM (`OpenAILLM`),
  - запускает агента через `run_agent_with_events` и возвращает `final_result` payload,
  - применяет доменные побочные эффекты (для `synopsis_manager` — запись live‑версии в БД через `psycopg2`).
- `backend/worker/run.py` — точка входа воркера RQ.
  - SimpleWorker включается флагом `AGENT_WORKER_SIMPLE=1` (рекомендуется для macOS).
  - Обычный Worker (с форком процессов) на Linux.

### Жизненный цикл задания

1. Клиент вызывает `POST /jobs/agents/{agent_id}/{version}` (или `POST /agents/.../synopsis?mode=background`).
2. API кладет в Redis задачу `run_agent_job(payload)` в очередь `AGENT_QUEUE` с параметрами `job_timeout` и `result_ttl`.
3. Воркер забирает задание из очереди и исполняет его.
4. Агент испускает события; по наступлению `final_result` задача формирует итоговый payload и (опционально) пишет доменный артефакт в БД.
5. По завершении статус в Redis меняется на `finished`, результат хранится в Redis до истечения `AGENT_RESULT_TTL`.
6. Клиент может либо:
   - поллить `GET /jobs/{jobId}` до `done|failed`,
   - либо сразу поллить доменный ресурс (например, `GET /sessions/{id}/synopsis`).

### Маппинг статусов RQ → API

- RQ: `queued|scheduled|deferred` → API: `queued`
- RQ: `started` → API: `running`
- RQ: `finished` → API: `done`
- RQ: `failed|stopped|canceled` → API: `failed`

При `done` поле `result` содержит итог задачи (dict). При `failed` поле `error` содержит краткое описание (последняя строка `exc_info`).

## Redis: устройство ключей

RQ использует стандартные ключи с префиксом `rq:`. Важно: конкретные имена некоторых регистров могут немного отличаться между версиями RQ, но основной набор стабилен.

- `rq:workers` (Set)
  - Содержит имена всех зарегистрированных воркеров.
  - Пример члена: `rq:worker:714ce0eb742a40e8a60e46ac52cf4b37`.

- `rq:worker:{worker_id}` (Hash)
  - Сведения о воркере: `hostname`, `ip_address`, `version`, `python_version`, `queues`, `state` (`idle|busy|...`), `last_heartbeat`, `pid`.
  - На скриншоте виден TTL, но обычно он не ограничен (обновляется сердцебиением).

- `rq:queue:{queue_name}` (List)
  - Очередь заданий (FIFO). Элементы — идентификаторы задач.
  - По умолчанию используем `queue_name = agents`.

- `rq:job:{job_id}` (Hash)
  - Метаданные задачи и сериализованные поля RQ: `status`, `created_at`, `enqueued_at`, `started_at`, `ended_at`, `timeout`, `result_ttl`, `data` (callable + args), `result` (сериализованный Python‑объект), `exc_info`.
  - Хеш удаляется по истечении `result_ttl` (или при явной очистке).

- Регистры очереди (Sorted Set / Set, зависят от версии RQ):
  - `rq:queue:{queue_name}:started` — выполняемые задачи
  - `rq:queue:{queue_name}:finished` — завершенные (на период удержания)
  - `rq:queue:{queue_name}:failed` — упавшие
  - `rq:queue:{queue_name}:scheduled` — отложенные к запуску
  - `rq:queue:{queue_name}:deferred` — с зависимостями
  - `rq:queue:{queue_name}:cancelled` — отмененные

Полезные приёмы:

```bash
# посмотреть воркеров
redis-cli SMEMBERS rq:workers

# метаданные конкретного воркера
redis-cli HGETALL rq:worker:<id>

# первые 10 job в очереди agents
redis-cli LRANGE rq:queue:agents 0 9

# статус и короткая причина падения
redis-cli HGET rq:job:<job_id> status
redis-cli HGET rq:job:<job_id> exc_info
```

## API, совместимые контракты

### Постановка в очередь

```http
POST /jobs/agents/{agent_id}/{version}
Content-Type: application/json

{
  "session_id": "...",          // опционально
  "memory": "backend|inmem",    // по умолчанию inmem
  "query": { ... },               // вход агента
  "apply_side_effects": true      // по умолчанию true
}

202 { "jobId": "..." }
```

### Статус

```http
GET /jobs/{jobId}

200 {
  "status": "queued|running|done|failed",
  "result": { ... }?,
  "error": "..."?
}
```

### JSON‑обёртка конкретного агента

```http
POST /agents/synopsis_manager/v1/synopsis?mode=background|sync

// background → 202 { jobId }, sync → 200 { ...payload... }
```

## Как это работает внутри задачи

- `run_agent_job(payload)` формирует окружение агента (память, LLM) и запускает общий раннер `run_agent_with_events`.
- Ожидаем событие `final_result` и возвращаем его payload как результат задачи.
- Для `synopsis_manager` выполняется побочный эффект: запись live‑версии конспекта в БД (через `psycopg2`).
  - Используются `DB_URL` или `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME`.
  - Если `session_id` отсутствует в `track_sessions`, запись пропускается (задача не падает).

## Диагностика

- Если на macOS падает «work‑horse terminated unexpectedly» — используйте SimpleWorker (`AGENT_WORKER_SIMPLE=1`). Он работает с Redis, но не форкает процессы.
- Смотрите логи процесса воркера (запускается через `make worker`).
- В `GET /jobs/{id}` поле `error` содержит последнюю строку трейсбека; полный стек — в логах воркера и в `rq:job:{id} -> exc_info`.
- Истёк `AGENT_RESULT_TTL` → `GET /jobs/{id}` вернёт 404 (ключ удалён). Полльте доменный ресурс вместо статуса, если важна устойчивость к TTL.

## Масштабирование и устойчивость

- Вертикально: поднимайте несколько процессов `make worker` (каждый процесс обрабатывает по одному job одновременно в SimpleWorker). На Linux можно отключить `AGENT_WORKER_SIMPLE` и использовать форкинг.
- Горизонтально: запускайте воркеры на нескольких машинах, указывая один `REDIS_URL` и общее имя очереди.
- Ретраи: можно реализовать на стороне API при enqueue (`retry` в payload) или добавить обёртку/регистры RQ.
- Rate‑limit/квоты: реализуются на уровне API/бизнес‑логики перед enqueue.

## Расширение

- Добавить новый агент — не требует изменений в воркере: задайте `{ agent_id, version }` в `POST /jobs/agents/...`.
- Новые побочные эффекты — расширяйте `run_agent_job` условной веткой по `agent_id` или переносите в соответствующий агент/инструмент.
- Несколько очередей (приоритеты) — заведите доп. переменные `AGENT_QUEUE_HIGH/LOW` и собственные эндпоинты enqueue.

## Известные ограничения

- Нет идемпотентности: повторный вызов создаст новое задание. Рекомендация: добавлять клиентский ключ идемпотентности и проверять/де‑дублировать перед enqueue. 
- Результаты исчезают по TTL (`AGENT_RESULT_TTL`). Полльте доменные ресурсы, если важна долговременная доступность итогов.
- SimpleWorker обрабатывает по одному заданию на процесс. Для большей параллельности — несколько процессов.

## Примеры

```bash
# enqueue
curl -sX POST http://localhost:8000/jobs/agents/synopsis_manager/v1 \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id": "dev-s1",
    "memory": "inmem",
    "query": { "action": "create", "params": { "title": "Intro", "description": "...", "goal": "...", "focus": "theory", "tone": "friendly" }, "plan": ["Введение"] }
  }'

# статус
curl -s http://localhost:8000/jobs/<JOB_ID> | jq
```

---

// AICODE-TODO: добавить опциональные ретраи с экспоненциальным бэкоффом и идемпотентность по ключу `agent:<id>@<version>:session:<sid>`.


