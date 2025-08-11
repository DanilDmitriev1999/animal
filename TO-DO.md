# AICODE-TODO: Архитектура фоновых запусков агентов (не блокировать UI/HTTP)

## Цели
- Перевести тяжёлые вызовы (LLM/инструменты) в фоновые задания, чтобы HTTP‑запросы завершались мгновенно и не деградировали производительность UI.
- Гарантировать сохранение доменных артефактов (например, `synopsis`) в БД и возможность безопасного повторного запуска.

## Дизайн (высокоуровневый)
- Вводим очередь заданий (Redis + RQ или Dramatiq; базово RQ).
- Выделяем отдельный процесс worker (`agents-worker`), который исполняет задания: запускает агента через общий `run_agent_with_events`, обрабатывает события, сохраняет итог в доменные таблицы.
- HTTP-роуты на бэкенде возвращают 202 Accepted + `jobId`, не дожидаясь результата. Фронт наблюдает статус задания и/или читает готовый доменный артефакт.

## БД (новые таблицы)
- `jobs`:
  - `id UUID PK`, `type TEXT` (напр. `agent:synopsis_manager`), `status TEXT` (`queued|running|done|failed`), `payload_json JSONB`, `result_json JSONB`, `error_text TEXT`, `session_id UUID NULL`, `created_at/updated_at`.
  - Индексы: `(status, created_at)`, `(session_id, type)`.
- (Опционально) `job_locks`/`idempotency_keys` — предотвращение дублей по ключу `agent+session`.

## Queue/Worker
- Пакет `backend/worker/`:
  - `queue.py` — обёртка RQ (Redis URL из `REDIS_URL`).
  - `tasks.py` — функции: `run_agent_job(agent_id, version, session_id, query, memory)` → выполняет `run_agent_with_events` и сохраняет итог в БД (как уже сделано для `synopsis`).
  - Команда запуска: `make worker` → `python -m backend.worker.run`.
- Конфиг: `AGENT_WORKER_CONCURRENCY`, `AGENT_JOB_TTL`, `AGENT_JOB_RETRIES`.

## Backend API
- Новый маршрут постановки в очередь:
  - `POST /jobs/agents/{id}/{version}` → тело `{ session_id, query, memory }` → 202 `{ jobId }`.
- Чтение статуса:
  - `GET /jobs/{jobId}` → `{ status, error?, result? }`.
- Для `synopsis_manager`: оставить существующий JSON‑роут, но добавить query‑параметр `?mode=background|sync` (по умолчанию `background`), который кладёт задание в очередь и возвращает `jobId`.
- Побочный эффект остаётся прежним: worker по завершении пишет live‑версию в `synopses/synopsis_versions`.

## Frontend
- Для генерации конспекта:
  - вызывать `enqueue` (или `agents/.../synopsis?mode=background`), показывать тост «Формируем конспект…»;
  - опрос статуса `GET /jobs/{id}` либо сразу поллинг доменного ресурса `GET /sessions/{sessionId}/synopsis` с бэкоффом;
  - при готовности — подменить плейсхолдер реальными данными.
- UI‑индикатор в оверлее «Конспект»: «формируется…», состояние не триггерит повторную генерацию.

## Производительность и устойчивость
- Ограничение конкуренции на worker через `AGENT_WORKER_CONCURRENCY`.
- Квоты/Rate‑limit на пользователя и на тип задания.
- Таймауты LLM, повторные попытки (экспоненциальный бэкофф, напр. 2/4/8 мин, максимум 3 ретрая).
- Идемпотентность: ключ `agent:<id>@<version>:session:<sid>` — если задание в статусе `queued|running`, новое не создаём; если `failed|done` — создаём новое.

## Наблюдаемость
- Метрики: счётчики по `jobs_total{type,status}`, `job_duration_seconds`.
- Логи: привязка `jobId` к `trace_id` агента; запись событий агента в трейсинг.

## Безопасное внедрение (по шагам)
1) Добавить таблицу `jobs` и минимальный worker с заглушкой (пустое задание) — smoke.
2) Перевести `synopsis_manager` на очередь (режим `background` по умолчанию; `sync` оставить для отладки).
3) Добавить опрос статуса/доменного ресурса на фронте.
4) Протестировать на 100+ параллельных заданиях; настроить квоты.
5) Расширить на другие агентов (планировщик/аналитика/поиск источников).

## Конфигурация/инфра
- `docker-compose`: сервис `redis`, сервис `agents-worker` (запуск воркера).
- ENV: `REDIS_URL`, `AGENT_WORKER_CONCURRENCY`, `AGENTS_DEFAULT_MODEL` (как есть).

## Тесты
- Юнит: создание job, выполнение task c мок‑LLM, запись в `synopses`.
- Интеграция: e2e — POST enqueue → поллинг статуса → готовый конспект доступен по REST.
