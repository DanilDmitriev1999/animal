# База данных: схема и скрипты

// AICODE-NOTE: Этот файл описывает схему БД и порядок запуска SQL-скриптов для локальной разработки.

## Быстрый старт

1) Убедитесь, что PostgreSQL поднят через docker-compose (`postgres:15`).
2) Скопируйте пример окружения и при необходимости отредактируйте:

```
cp backend/env.example backend/.env
```

3) Установите зависимости для Python-скриптов БД (используется venv из корня проекта — `./venv`):

```
make db-install
```

4) Инициализируйте БД (reset + schema + seed) через Python CLI:

```
make db-init
```

Альтернативно, по шагам:

```
make db-reset
make db-schema
make db-seed
```

Можно переопределить строку подключения через переменную окружения `DB_URL` или раздельные `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME`. Переменные читаются из `.env` и/или текущего окружения.

## Обзор схемы

- `users` — пользователь (пока гость через `device_id`).
- `tracks` — каталог треков (описание программы).
- `track_roadmap_items` — пункты роадмапа конкретного трека.
- `chat_templates` — LLM-шаблоны (global | track | createTrack) + версии.
- `track_sessions` — сессия пользователя внутри трека (состояние UI, связи с чатами/конспектами).
- `chat_threads` — ветка чата по табу `chat|practice|simulation` на одну сессию.
- `chat_messages` — сообщения внутри ветки (роль `user|assistant|tool`, `meta_json`).
- `synopses` — конспекты: один «live» и множество «snapshot/imported» на сессию.

### Ключевые связи

- `users 1--* track_sessions` (один пользователь — много сессий по трекам).
- `tracks 1--* track_sessions` (сессии на базе трека).
- `tracks 1--* track_roadmap_items` (упорядоченные пункты).
- `track_sessions 1--* chat_threads` (по одному на каждый таб).
- `chat_threads 1--* chat_messages`.
- `track_sessions 1--* synopses` (live и snapshots).
- `tracks 1--* chat_templates` со `scope='track'`; также есть `scope='global'` и `scope='createTrack'`.

## Назначение таблиц

- `users`
  - `device_id` — временный идентификатор до внедрения регистрации.
  - `settings_json` — любые пользовательские настройки.

- `tracks`
  - Базовые атрибуты программы: `slug`, `title`, `description`, `goal`.

- `track_roadmap_items`
  - `position` — порядок отображения; индекс `(track_id, position)`.

- `chat_templates`
  - `scope` — область применения (`global|track|createTrack`).
  - `content` — системный/инструкционный промпт.
  - `variables_json` — плейсхолдеры и значения по умолчанию.

- `track_sessions`
  - `active_tab` — какой таб открыт (`chat|practice|simulation`).
  - `sidebar_visible` — видимость правой панели.

- `chat_threads`
  - Уникальна пара `(session_id, tab)`.

- `chat_messages`
  - Сообщения с ролью (`user|assistant|tool`), `meta_json` для источника, токенов и т.п.

- `synopses`
  - `origin` ∈ {`live`,`snapshot`,`imported`}.
  - `items_json` — массив элементов типа, совместимого с `LiveSynopsis` во фронте.

## Примечания по миграциям

- Все таблицы и индексы создаются idempotent (`IF NOT EXISTS`).
- Используются перечисления `template_scope`, `chat_tab`, `message_role`, `synopsis_origin`.
- Расширение `pgcrypto` — для `gen_random_uuid()`.

## Побочные эффекты разговорных агентов

- JSON‑маршруты `POST /agents/mentor_chat/v1/reply`, `/agents/practice_coach/v1/hint`, `/agents/simulation_mentor/v1/turn` при флаге `apply_side_effects=true` и наличии `session_id` записывают результат ответа ассистента в соответствующую ветку `chat_threads` (`chat|practice|simulation`) как запись в `chat_messages` с ролью `assistant` и `meta_json = { agentId, version }`.
- Если `session_id` отсутствует или ветка не найдена — запись пропускается (без ошибок).


