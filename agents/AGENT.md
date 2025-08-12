// AICODE-NOTE: Единый документ по агентам. Минимализм в реализации — приоритет.

### Цель

Сделать простой и расширяемый слой «агентов» для AI Learning:
- **единый чат** и шаги без обязательного user-сообщения (assistant-only);
- **стриминг только событий** (не токенов);
- **реестры** агентов/инструментов/LLM-вызовов в коде (авто‑регистрация);
- **память обязательна** у каждого агента и подменяема;
- **трейсинг** и события пишутся бэкендом в PostgreSQL (см. `backend/DB.md`).

Работает как питон‑пакет `agents/`, который импортируется из бэкенда (FastAPI). В ближайшее время бэкенд предоставляет только CRUD по трекам/чатам (см. `backend/API.md`); маршруты запуска агентов будут добавлены отдельно.

---

### Окружение

Используем dotenv. Пример — `agents/env.example`.

- `OPENAI_API_KEY` — ключ для провайдера.
- `OPENAI_BASE_URL` — базовый URL прокси OpenAI (обязательно; напр. `https://my-proxy/v1`).
- `OPENAI_ORG` — опционально.
- `AGENTS_DEFAULT_MODEL` — модель по умолчанию (напр. `gpt-4o-mini`).
- `REDIS_URL` — `redis://localhost:6379/0`.
- `AGENTS_LOG_LEVEL` — `INFO` по умолчанию.

Загрузка `.env` происходит автоматически при импорте пакета `agents` (см. `agents/__init__.py`).
Поддерживаются `.env` из корня репозитория и из директории `agents/`.

---

### Минимальная архитектура

- Код определений живёт в `agents/` и версионируется Git’ом.
- Факты исполнения (трейсы, события, llm/tool invocations) сохраняет бэкенд (PostgreSQL, см. `backend/DB.md`).
- Короткая история чата может кэшироваться в Redis; базово память загружает все сообщения для сессии из бэкенда.
- Стрим наружу — события, которые агент yield’ит; бэкенд ретранслирует по SSE/WS (маршруты будут добавлены).

---

### Структура пакета

```text
agents/
  __init__.py
  registry.py          # регистрация агентов/инструментов; get_* по (id, version)
  base.py              # протоколы Event, AgentBase и базовый класс AgentABC
  runner.py            # run_agent_with_events(): before/after, трейс‑хуки, yield событий
  callbacks.py         # CallbackManager (before/after для llm/tool/agent)
  tracing.py           # интерфейс для бэкенд‑адаптера трейсинга
  llm/
    __init__.py        # экспорт абстракций и реализаций LLM
    base.py            # LLMClientBase/LLMClientABC — общий интерфейс и базовая абстракция
    openai_llm.py      # реализация OpenAILLM (создание внутреннего SDK‑клиента внутри реализации)
  memory/
    __init__.py
    base.py            # BaseMemory(load_dialog/append/get_kv/set_kv)
    redis_short_term.py# опциональная краткая память в Redis
  roles/
    policy.py          # RolePolicy и DialogueBuilder
  tools/
    base.py            # ToolBase, pydantic схемы
    search_web/        # пример готового инструмента
  patterns/            # опционально: миксины/скелеты паттернов
    __init__.py
    react.py           # Reason/Act helpers (SO-схемы Decision/Verdict)
    repl.py            # ВРЕМЕННО ОТКЛЮЧЕНО (заглушка)
    planner_executor.py# ВРЕМЕННО ОТКЛЮЧЕНО (заглушка)
    workflow.py        # последовательный и циклический workflow (каждый шаг — отдельный агент)
  under_hood/          # конкретные агенты (авто‑регистрация при импорте)
    learning_planner/
      agent.py         # фабрика @register_agent("learning_planner","v1")
      prompts.yaml
```

> Авто‑регистрация: при старте бэкенда вызывается простая `autodiscover()` из `agents/` (импорт всех под‑пакетов в `under_hood/*`). Фабрики выполнят декораторы регистрации.

---

### Контракты (минимум)

```python
# base.py (сокращённо)
class Event(BaseModel):
    event: str
    session_id: str
    trace_id: str
    payload: dict | None = None

class AgentBase(Protocol):
    id: str
    version: str
    memory: "BaseMemory"
    role_policy: dict
    meta: dict
    async def run(self, **kwargs) -> dict: ...
    async def run_with_events(self, **kwargs) -> AsyncIterator[Event]: ...

class AgentABC(ABC):
    id: str = "base"
    version: str = "v1"

    def __init__(self, memory: "BaseMemory", *, role_policy: dict | None = None, meta: dict | None = None, llm: Any | None = None) -> None: ...

    def emit(self, event: str, session_id: str, *, payload: dict | None = None, trace_id: str = "") -> Event: ...

    async def run(self, **kwargs) -> dict: ...  # оборачивает run_with_events

    async def run_with_events(self, *, session_id: str, **ctx) -> AsyncIterator[Event]:
        # Гарантирует стартовое событие и финальное `final_result` при отсутствии
        yield self.emit("start_agent", session_id, payload={"agent": self.id, "version": self.version})
        async for ev in self._run(session_id=session_id, **ctx):
            yield ev
        # (гарантия финала оформлена в реальной реализации)

    @abstractmethod
    async def _run(self, *, session_id: str, **ctx) -> AsyncIterator[Event]: ...  # реализуется наследниками

# memory/base.py
class BaseMemory(Protocol):
    async def load_dialog(self, session_id: str, role_policy: dict) -> list[dict]: ...
    async def append(self, session_id: str, messages: list[dict]) -> None: ...
    async def set_kv(self, session_id: str, key: str, value: Any) -> None: ...
    async def get_kv(self, session_id: str, key: str) -> Any: ...
```

Диалог собирается через `DialogueBuilder` с учётом `RolePolicy` и может не требовать user‑сообщений между шагами (assistant‑only). При необходимости добавляется синтетический user (`"continue:<step_id>"`).

---

### LLM‑абстракция

Введён единый интерфейс и базовый класс для LLM:

- `LLMClientABC` — контракт: `chat`, `chat_structured`, `chat_with_tools`, `vision_analyze`.
- `LLMClientBase` — создаёт внутренний SDK‑клиент в `__init__` через `_create_client(...)`.
- Реализация по умолчанию — `OpenAILLM`.

Пример инициализации и передачи в агента:

```python
from agents.llm import OpenAILLM
from agents.registry import get_agent

llm = OpenAILLM()  # SDK‑клиент создаётся внутри реализации
agent = get_agent("learning_planner", "v1", memory=memory, llm=llm)
```

Возможности реализации:
- структурированный ответ (`chat_structured`) — возвращает распарсенный JSON и исходный ответ;
- вызов инструментов (`chat_with_tools`) — поддержка tool_calls с циклом до `max_steps`;
- обработка изображений (`vision_analyze`).

Подсчёты токенов/стоимости — на стороне трейсинга/бэкенда.

---

### События (стрим‑контракт)

Агент отдаёт только статусы/данные шагов. Пример:

```json
{"event":"start_agent","session_id":"s1","trace_id":"...","payload":{"message":"Запуск"}}
{"event":"planning","session_id":"s1","trace_id":"...","payload":{"message":"Формируем план"}}
{"event":"tool_selection","session_id":"s1","trace_id":"...","payload":{}}
{"event":"final_result","session_id":"s1","trace_id":"...","payload":{"plan":{...}}}
{"event":"error","session_id":"s1","trace_id":"...","payload":{"message":"..."}}
```

Бэкенд сохраняет события/факты в БД по схемам из `backend/DB.md` и ретранслирует по SSE/WS.

---

### Память

- Базовая реализация: загрузка всей истории сообщений из бэкенда для `session_id` (и, при необходимости, `tab`). Это самая простая и надёжная стратегия.
- Опционально: `RedisShortTerm` — хранит последние N сообщений по ключу `chat:{session_id}`. Можно использовать как кэш поверх бэкенда.

История дополняется результатами шага агента (assistant‑сообщения с `name=<step_id>`), чтобы следующие шаги могли ссылаться на контекст.

---

### Интеграция с текущим бэкендом/фронтом

- Сейчас доступны только эндпоинты работы с треками/сессиями/сообщениями (см. `backend/API.md`).
- Агенты подключаются как внутренний пакет: бэкенд импортирует `agents`, создаёт `memory` и запускает раннер.
- Маршруты запуска агентов будут добавлены в FastAPI позднее (см. TODO). Фронт сможет вызывать их для генерации плана/аналитики и получать события через SSE.

Минимальный вызов из бэкенда:

```python
from agents import autodiscover
from agents.registry import get_agent
from agents.runner import run_agent_with_events

autodiscover()
agent = get_agent("learning_planner","v1", memory=SomeMemory(...))
async for ev in run_agent_with_events(agent, session_id="s1", topic="Python"):
    yield ev  # отправить в SSE/WS
```

---

### Авто‑регистрация и under_hood

- Каждый агент/инструмент предоставляет `factory(memory)` и декорируется `@register_agent(id, version)` / `@register_tool(id, version)`.
- `under_hood/*/agent.py` импортируется на старте (авто‑дискавери), декоратор регистрирует фабрику в реестре.
- Вызов по API происходит по паре `(id, version)`.

---
### Как добавить нового продуктового агента

// AICODE-NOTE: Универсальная инструкция — не привязана к конкретному агенту.

1) Определите идентификаторы
- **id**: строка в `kebab_case` или `snake_case` (например, `mentor_chat`).
- **version**: строка версии (например, `v1`).

2) Создайте директорию агента
```
agents/under_hood/<agent_id>/
  __init__.py
  agent.py
  prompts.yaml                # system‑промпт (опц., но рекомендуется)
  prompts_developer.yaml      # developer‑промпт (опц.)
  so_schema.py                # Pydantic‑схемы для строгого вывода (опц.)
```

3) Зарегистрируйте фабрику и класс агента
- Фабрика помечается декоратором `@register_agent(id, version)` и возвращает инстанс класса вашего агента.
- Класс наследуется от `AgentABC` и реализует метод `_run(...)`, который `yield`‑ит события и завершает `final_result`.

Пример минимального скелета:
```python
from __future__ import annotations

import os
from typing import AsyncIterator

from ...base import AgentABC, Event
from ...registry import register_agent, get_prompt
from ...roles.policy import DialogueBuilder, to_openai_chat_messages


@register_agent("my_agent", "v1")
def factory(memory, role_policy=None, meta=None, llm=None):
    # LLM и прочие зависимости подаются извне
    return MyAgent(memory=memory, role_policy=role_policy or {}, meta=meta or {}, llm=llm)


class MyAgent(AgentABC):
    id = "my_agent"
    version = "v1"

    async def _run(self, *, session_id: str, user_message: str = "", **ctx) -> AsyncIterator[Event]:
        step = "my_step"
        # Промежуточное событие прогресса
        yield self.emit(step, session_id, payload={"message": "Готовим ответ"})

        # 1) Соберите диалог с учётом памяти и промптов
        system_text = get_prompt("my_agent.system")  # если используете Prompt Registry
        developer_text = (get_prompt("my_agent.developer").format(message=user_message or ""))
        dialog = await DialogueBuilder.build(
            self.memory, session_id, self.role_policy, step,
            system_text=system_text, developer_text=developer_text,
        )

        # 2) Вызов LLM (клиент прокинут через фабрику; модель — через meta/env)
        model = self.meta.get("model") or os.getenv("AGENTS_DEFAULT_MODEL", "gpt-4o-mini")
        messages = to_openai_chat_messages(dialog)
        response = await self.llm.chat(messages=messages, model=model)
        text = response.result if isinstance(response.result, str) else str(response.result)

        # 3) Сохраните результат шага в память и отдайте финальное событие
        await self.memory.append(session_id, [{"role": "assistant", "name": step, "content": {"message": text}}])
        yield self.emit("final_result", session_id, payload={"message": text})
```

4) Добавьте промпты в YAML (Prompt Registry)
- Файлы кладутся рядом с агентом и подхватываются `autodiscover_prompts()` автоматически.
- Структура файла:
```yaml
id: my_agent.system
versions:
  v1: |
    Ты продуктовый AI‑агент. Веди диалог кратко и по делу.
meta:
  owner: core
```

5) Инициализация и запуск
- В рантайме вызывается `autodiscover_prompts()` и `autodiscover()` (делается бэкендом/CLI).
- Получение и запуск:
```python
from agents import autodiscover, autodiscover_prompts
from agents.registry import get_agent
from agents.memory import InMemoryMemory
from agents.llm import OpenAILLM
from agents.runner import run_agent_with_events

autodiscover_prompts(); autodiscover()
agent = get_agent("my_agent", "v1", memory=InMemoryMemory(), llm=OpenAILLM())
async for ev in run_agent_with_events(agent, session_id="s1", user_message="Привет"):
    print(ev.model_dump())
```

6) Соглашения и требования
- Агент обязан принимать `memory` и `session_id`; `llm` и `meta` — опционально, но предпочтительно через фабрику.
- `AgentABC` сам отправит `start_agent`; вы генерируете шаги и `final_result`.
- Старайтесь разделять этапы на небольшие шаги и писать в память результат каждого шага `{"role":"assistant","name":"<step>",...}`.
- Для воспроизводимости используйте Prompt Registry, а не хардкод строк в коде.

7) Отладка через CLI
```bash
python3 -m agents.cli list              # проверка авто‑регистрации
python3 -m agents.cli run my_agent v1 \
  --session dev-s1 --query "Привет" --memory inmem
```

---

### Паттерны (скелеты для переиспользования)

Директория `patterns/` содержит минимальные примитивы, которые можно миксовать в конкретных агентах или переопределять.

- `react.py` — `ReActAgentBase` (Decision→Action→Observation→Verdict) + Pydantic‑схемы. Наследуется от `AgentABC`.
- `workflow.py` — `SequentialWorkflowAgentBase` (последовательные шаги) и `LoopWorkflowAgentBase` (цикл до done). Наследуются от `AgentABC`.
- `repl.py` и `planner_executor.py` — временно отключены (оставлены заглушки для совместимости импортов).

Все паттерны — класс‑скелеты агентов на базе `AgentABC`: не стримят токены, отдают только события, совместимы с общим раннером.

Соглашение по событиям в паттернах:
- старт: `start_agent` (добавляется автоматически базовым классом);
- прогресс шагов: паттерн‑специфичные события (`planning`, `execution`, `react_step_*`, `repl_step`, `workflow_step_*`, `loop_step_*`);
- завершение: `final_result` c итоговыми данными.

Минимальные примеры использования паттернов:

```python
# ReAct
from agents.patterns import ReActAgentBase

async def llm_call(prompt_id: str, **ctx) -> dict: ...
react = ReActAgentBase(memory=memory, llm_call=llm_call, tools={})
```

```python
# Последовательный workflow (каждый шаг — агент)
from agents.patterns import SequentialWorkflowAgentBase

# some agents
agent_a = get_agent("agent_a", "v1", memory=memory, llm=llm)
agent_b = get_agent("agent_b", "v1", memory=memory, llm=llm)

wf = SequentialWorkflowAgentBase(memory=memory, steps=[("a", agent_a), ("b", agent_b)])
```

```python
# Циклический workflow (агенты plan/act/check)
from agents.patterns import LoopWorkflowAgentBase

plan_agent = get_agent("plan", "v1", memory=memory, llm=llm)
act_agent = get_agent("act", "v1", memory=memory, llm=llm)
check_agent = get_agent("check", "v1", memory=memory, llm=llm)

loop = LoopWorkflowAgentBase(memory=memory, plan_agent=plan_agent, act_agent=act_agent, check_agent=check_agent)
```

---

### Как дополнять паттерны и зачем они нужны

Паттерны — это переиспользуемые скелеты бизнес‑логики агента. Они ускоряют разработку и стандартизируют события.

Как расширять существующие паттерны:
- унаследуйтесь от базового паттерна и переопределите поведение (например, подмените функции шагов через DI);
- добавляйте свои события через `self.emit(...)` на ключевых этапах;
- соблюдайте соглашения: `start_agent` → шаги → `final_result` и структурируйте `payload` как Pydantic‑модели, если данные стабильны;
- все I/O выносите в переданные коллбэки/инструменты, чтобы паттерн оставался тонким.

Как создать новый паттерн:
```python
from agents.base import AgentABC, Event
from typing import AsyncIterator

class MyPatternBase(AgentABC):
    id = "my_pattern_base"
    version = "v1"

    async def _run(self, *, session_id: str, **ctx) -> AsyncIterator[Event]:
        # ваши шаги и события
        yield self.emit("my_step", session_id, payload={"x": 1})
        yield self.emit("final_result", session_id, payload={"ok": True})
```

Зачем использовать паттерны:
- **скорость**: меньше шаблонного кода; готовые события/циклы;
- **единообразие**: фиксированный контракт событий и интеграция с раннером/трейсингом;
- **тестируемость**: шаги вынесены в функции/инструменты, легко мокать;
- **расширяемость**: можно миксовать (`HITLMixin`) и создавать гибриды.

---

### Версионирование промптов (план и процесс)

// AICODE-NOTE: Минималистичный, но удобный процесс без лишней сложности.

1) Источник истинны — файлы YAML в коде:
   - Глобальные: `agents/prompts/*.yaml`
   - Агент‑специфичные: `agents/under_hood/<agent>/prompts.yaml`
   - Структура:
     ```yaml
     id: learning_planner.system
     versions:
       v1: |
         Ты образовательный ассистент...
       v2: |
         Обновлённая версия...
     meta:
       owner: core
     ```
2) Загрузчик (Prompt Registry):
   - При старте вызывается `prompts.autodiscover_prompts()` (по аналогии с агентами), читает все YAML и строит маппинг `(id, version) -> text` + `latest`.
   - API: `get_prompt(id, version=None)` — вернуть указанную версию или последнюю.
3) Использование в агентах:
   - Агент запрашивает system/developer промпты через `get_prompt()` вместо хардкода.
   - `DialogueBuilder` использует текст промпта напрямую.
4) Снапшот в трейсинг:
   - Перед LLM‑вызовом в after/before‑колбэке сохраняем `prompt_id`, `prompt_version`, `prompt_text_snapshot` в событие LLM (см. `backend/DB.md: llm_invocations`).
5) (Опционально) Централизованное хранение в БД:
   - Таблица `prompt_versions` уже предусмотрена; можно добавить REST CRUD в бэкенд.
   - На первом этапе достаточно YAML + снапшота в трейсинге для воспроизводимости.

Результат: фиксированная, воспроизводимая версия промпта на момент вызова, простое редактирование через YAML и минимальный runtime‑код.

---

### CLI

Для локальной проверки регистрации и запуска агентов есть простой CLI.

Подготовка:
- Создайте `agents/.env` или корневой `.env` с переменными из `agents/env.example`.
- Убедитесь, что бэкенд API доступен на `AGENTS_BACKEND_API_URL` (для `BackendMemory`).

Запуск:
- Список и проверка авто‑регистрации:
  ```bash
  python -m agents.cli list
  ```
- Запуск агента с выводом событий в stdout:
  ```bash
  python -m agents.cli run learning_planner v1 --session dev-s1 --topic "Python"
  ```

CLI по умолчанию использует `BackendMemory` (нужен запущенный бэкенд API),
но можно выбрать in-memory режим без бэкенда:
```bash
python -m agents.cli run learning_planner v1 --session dev-s1 --topic "Python" --memory inmem
```

---

### Roadmap/TO‑DO (живой список)
// AICODE-NOTE: Если задача выполнена — помечать [x] и держать список актуальным.

// AICODE-TODO: Ближайшие шаги (handoff чек‑лист для следующего исполнителя)
- [ ] FastAPI SSE‑маршрут запуска агента
  - Где: `backend/app/main.py`
  - Эндпоинт: `POST /run/agent/{id}/{version}?memory=backend|inmem`
  - Тело: `{ "session_id": string, "payload": object }`
  - Действия: `autodiscover()` → собрать `memory` (по query) → `get_agent()` → `run_agent_with_events()` → SSE
  - Критерии приёмки:
    - curl получает поток событий: `start_agent`, `planning`, `final_result`
    - `--memory=inmem` работает без запущенного бэкенда
    - Ошибки возвращаются как SSE `error`
- [ ] Tracing‑адаптер минимальный
  - Где: `agents/tracing.py`
  - Добавить точку расширения: `Trace.set_sink(callable)`; по умолчанию no‑op, опционально POST в бэкенд `/tracing` (когда появится)
  - Критерии: юнит‑тест фиксирует вызовы sink на `event()` и `finish()`
- [ ] Инструмент `tools/search_web`
  - Где: `agents/tools/search_web/`
  - Простая реализация: мок/заглушка (или внешний поиск), регистрация в реестре
  - Интеграция: вызвать из `learning_planner` после плана и добавить `sources` в результат
  - Критерии: CLI run выводит `sources[]`
- [ ] Тесты (pytest)
  - `tests/test_registry.py`: регистрация/получение агента и инструмента
  - `tests/test_memory_inmem.py`: append/load_dialog happy‑path
  - `tests/test_runner_contract.py`: поток событий содержит `start_agent` → `final_result`
  - Критерии: локальный запуск `pytest -q` зелёный
- [ ] Документация API
  - Где: `backend/API.md`
  - Добавить раздел про `POST /run/agent/...` (формат, SSE‑пример)
  - Критерии: пример команды `curl` повторяемый
- [ ] Интеграция фронта `/tracks/create`
  - Где: `frontend/src/app/tracks/create/page.tsx`
  - Вызов нового SSE‑маршрута для генерации плана; отобразить события статусом (toaster/overlay)
  - Критерии: happy‑path показывает план и источники
- [ ] Зависимости и окружение
  - Убедиться, что в `requirements.txt` (или соответствующем `pyproject`) есть `openai`, `httpx`, `python-dotenv`, `redis`
  - Проверка: CLI запускается в чистом окружении по README

- [x] Реализация `registry.py` с декораторами `register_agent/register_tool` и `get_*`.
- [x] `base.py`: протоколы `AgentBase`, `Event`.
- [x] `memory/base.py` + `RedisShortTerm` + `BackendMemory` (HTTP к текущему API).
- [x] `roles/policy.py` и `DialogueBuilder` (assistant‑only + синтетический user по флагу).
- [x] `runner.py` с колбэками и событиями.
- [x] `callbacks.py` (минимум).  
  [ ] Адаптер трейсинга `tracing.py` → запись в БД через бэкенд (`traces/events/...`).
- [x] LLM‑клиент на `openai` с `OPENAI_BASE_URL` (без стрима токенов).
- [x] `patterns/`: скелеты `hitl.py`, `react.py`, `repl.py`, `planner_executor.py`.
- [x] Обновлён `agents/env.example` (+ `AGENTS_BACKEND_API_URL`).
- [x] Пример агента `under_hood/learning_planner` с интеграцией памяти и LLM.
- [ ] Пример использования `hitl` и его использование из агента.
- [x] CLI: `python -m agents.cli list|run` — симуляция запуска агента.
- [ ] Простые юнит‑тесты: реестр, BackendMemory, контракт событий раннера.
- [ ] Бэкенд‑маршрут: `POST /run/agent/{id}/{version}?stream=sse` (SSE) — минимальная реализация.
- [ ] Интеграция `/tracks/create` на фронте с этим маршрутом (см. `frontend/src/app/tracks/create/page.tsx`).
- [ ] Prompt Registry
  - [x] Реализовать `agents/prompts/registry.py` с `autodiscover_prompts()` и `get_prompt(id, version=None)`.
  - [x] Описать YAML‑схему и добавить пример `agents/prompts/example.yaml` и `agents/under_hood/learning_planner/prompts.yaml`.
  - [x] Интегрировать в `learning_planner` (заменить хардкод system/dev промптов).
  - [ ] Добавить снапшот промпта в трейсинг (`llm_invocations.prompt_text_snapshot`, `prompt_id`, `prompt_version`).
  - [ ] (Опц.) Бэкенд CRUD по `prompt_versions` в `backend/API.md` и FastAPI.

---

### Ограничения и принципы

- Не усложняем. Первым делом — рабочий happy‑path без лишних абстракций.
- Все версии и ID — обычные строки в коде; БД хранит только факты исполнения.
- Стримим только события — токены не нужны.
- Каждое исполнение агента обязано иметь `memory` и `session_id`.


