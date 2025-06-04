# AI Learning Platform - Backend Documentation

> **Подробная техническая документация backend'а для разработчиков**

## 🏗️ Архитектура Backend

### Обзор компонентов
- **Framework**: FastAPI + AsyncIO
- **Database**: PostgreSQL с SQLAlchemy ORM
- **WebSocket**: Real-time чат с AI
- **AI Integration**: OpenAI API с полной интеграцией
- **Authentication**: JWT токены + гостевой режим
- **Architecture**: Clean Architecture с разделением на роутеры/сервисы

### Структура проекта
```
backend/
├── routers/           # FastAPI роутеры (API endpoints)
│   ├── auth.py       # Аутентификация и авторизация
│   ├── tracks.py     # Управление треками обучения
│   ├── chat.py       # API чата и сессий планирования
│   └── ai_service.py # AI интеграция и LLM endpoints
├── services/          # Бизнес-логика
│   ├── chat_service.py    # Управление чатом и WebSocket
│   └── openai_service.py  # Интеграция с OpenAI API
├── models/           # Модели данных и БД
├── utils/            # Утилиты и конфигурация
│   └── config.py     # Настройки приложения
└── main.py           # Точка входа FastAPI приложения
```

---

## 🔗 API Endpoints

### 🔐 Authentication (`/api/auth`)

#### `POST /api/auth/register`
**Регистрация нового пользователя**

**Параметры:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "first_name": "Иван",
  "last_name": "Петров"
}
```

**Ответ:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "Иван",
    "last_name": "Петров",
    "role": "student",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Бизнес-логика:**
1. Проверка существующего email
2. Хеширование пароля (bcrypt)
3. Создание записи пользователя
4. Создание AI конфигурации по умолчанию
5. Генерация JWT токена

#### `POST /api/auth/login`
**Вход пользователя**

**Параметры:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Ответ:** Аналогичен `/register`

#### `POST /api/auth/guest-login`
**Вход в гостевом режиме**

**Параметры:** Нет

**Ответ:**
```json
{
  "access_token": "guest_token",
  "token_type": "bearer",
  "user": {
    "id": "guest_uuid",
    "email": "guest_xxx@guest.com",
    "first_name": "Гость",
    "last_name": "Пользователь",
    "role": "student",
    "is_guest": true
  }
}
```

**Особенности гостевого режима:**
- Данные не сохраняются в БД
- Временные ID для сессий и чатов
- Полная функциональность AI

#### `GET /api/auth/me`
**Получение информации о текущем пользователе**

**Headers:** `Authorization: Bearer <token>`

---

### 📚 Learning Tracks (`/api/tracks`)

#### `GET /api/tracks`
**Получение всех треков пользователя**

**Headers:** `Authorization: Bearer <token>`

**Ответ:**
```json
[
  {
    "id": "track_uuid",
    "title": "Изучение Python",
    "description": "Основы программирования",
    "skill_area": "Python Programming",
    "difficulty_level": "beginner",
    "estimated_duration_hours": 30,
    "status": "planning",
    "user_expectations": "Хочу освоить основы",
    "ai_generated_plan": {...},
    "modules": [
      {
        "id": "module_uuid",
        "module_number": 1,
        "title": "Основы Python",
        "description": "Введение в синтаксис",
        "learning_objectives": ["Изучить переменные", "Понять циклы"],
        "estimated_duration_hours": 8,
        "status": "not_started",
        "ai_generated_content": {...},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

**Бизнес-логика:**
- Для гостей возвращает пустой массив
- Загружает модули с помощью `selectinload()`
- Сортирует модули по `module_number`

#### `POST /api/tracks`
**Создание нового трека**

**Параметры:**
```json
{
  "title": "Изучение Python",
  "description": "Основы программирования на Python",
  "skill_area": "Python Programming",
  "difficulty_level": "beginner",
  "estimated_duration_hours": 30,
  "user_expectations": "Хочу освоить основы для анализа данных"
}
```

**Ответ:** Объект трека (как в GET)

**Бизнес-логика:**
1. Валидация `difficulty_level` (beginner/intermediate/advanced)
2. Создание записи трека
3. **Автоматическая генерация AI плана** через OpenAI
4. Парсинг JSON ответа от AI
5. Сохранение плана в `ai_generated_plan`

**LLM интеграция:**
```python
# Автоматический вызов OpenAI после создания трека
openai_service = await create_openai_service(str(user_id))
plan_result = await openai_service.generate_course_plan(
    skill_area=track_data.skill_area,
    user_expectations=track_data.user_expectations,
    difficulty_level=track_data.difficulty_level,
    duration_hours=track_data.estimated_duration_hours
)
```

#### `GET /api/tracks/{track_id}`
**Получение конкретного трека**

#### `PUT /api/tracks/{track_id}`
**Обновление трека**

#### `DELETE /api/tracks/{track_id}`
**Удаление трека**

---

### 💬 Chat System (`/api/chat`)

#### `POST /api/chat/sessions`
**Создание чат-сессии для планирования**

**Параметры:**
```json
{
  "track_id": "track_uuid",
  "session_name": "Planning Session"
}
```

**Ответ:**
```json
{
  "id": "session_uuid",
  "track_id": "track_uuid",
  "session_name": "Planning Session",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### `POST /api/chat/chats`
**Создание нового чата в сессии**

**Параметры:**
```json
{
  "session_id": "session_uuid",
  "chat_name": "Course Planning",
  "chat_type": "planning"
}
```

**Chat Types:**
- `planning` - основной чат планирования курса
- `discussion` - обсуждение деталей
- `finalization` - финализация модулей

#### `GET /api/chat/sessions/{session_id}/chats`
**Получение всех чатов сессии**

#### `GET /api/chat/chats/{chat_id}/messages`
**Получение сообщений чата**

**Ответ:**
```json
[
  {
    "id": "message_uuid",
    "chat_id": "chat_uuid",
    "sender_type": "user", // "user" или "ai"
    "message_content": "Привет! Хочу изучить Python",
    "message_type": "text",
    "ai_model_used": null,
    "tokens_used": null,
    "timestamp": "2024-01-01T00:00:00Z"
  },
  {
    "id": "message_uuid_2",
    "chat_id": "chat_uuid",
    "sender_type": "ai",
    "message_content": "Отлично! Создам план изучения Python...",
    "message_type": "welcome",
    "ai_model_used": "gpt-4o-mini",
    "tokens_used": 450,
    "timestamp": "2024-01-01T00:00:01Z"
  }
]
```

#### `GET /api/chat/users/chats`
**Получение всех чатов пользователя с группировкой**

**Ответ:**
```json
[
  {
    "session_id": "session_uuid",
    "session_name": "Planning Session",
    "track_title": "Изучение Python",
    "track_id": "track_uuid",
    "session_created_at": "2024-01-01T00:00:00Z",
    "chats": [
      {
        "id": "chat_uuid",
        "chat_name": "Course Planning", 
        "chat_type": "planning",
        "status": "active",
        "message_count": 15,
        "last_message_at": "2024-01-01T12:00:00Z"
      }
    ]
  }
]
```

#### `POST /api/chat/sessions/{session_id}/switch-chat`
**Переключение на конкретный чат**

**Параметры:**
```json
{
  "chat_id": "target_chat_uuid"
}
```

#### `GET /api/chat/chats/{chat_id}/history`
**Получение истории чата во временной последовательности**

#### `POST /api/chat/sessions/{session_id}/restore-existing-chat`
**Восстановление существующего чата планирования**

**Ответ:**
```json
{
  "success": true,
  "has_existing_chat": true,
  "chat_id": "existing_chat_uuid",
  "chat_info": {
    "id": "chat_uuid",
    "chat_name": "Course Planning",
    "chat_type": "planning",
    "status": "active"
  },
  "history": [...], // Полная история сообщений
  "message_count": 15
}
```

---

### 🤖 AI Service (`/api/ai`)

#### `POST /api/ai/generate-plan`
**Генерация плана курса через AI**

**Параметры:**
```json
{
  "track_id": "track_uuid",
  "user_expectations": "Хочу изучить основы Python для анализа данных"
}
```

**Ответ:**
```json
{
  "success": true,
  "plan": {
    "course_description": "Комплексный курс Python...",
    "learning_objectives": ["Цель 1", "Цель 2"],
    "modules": [...],
    "practical_assignments": [...],
    "final_project": {...}
  },
  "tokens_used": 450
}
```

#### `POST /api/ai/welcome-message`
**Генерация приветственного сообщения от AI**

**Параметры:**
```json
{
  "session_id": "session_uuid",
  "user_id": "user_uuid",
  "skill_area": "Python Programming",
  "user_expectations": "Хочу освоить основы",
  "difficulty_level": "beginner",
  "duration_hours": 30
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Привет! Я твой AI-помощник... 📚",
  "chat_id": "created_chat_uuid",
  "tokens_used": 450
}
```

**LLM интеграция:**
1. Создается или получается чат типа "planning"
2. Генерируется структурированное приветствие с эмодзи
3. Сообщение сохраняется в БД с метаданными
4. Возвращается `chat_id` для дальнейшего использования

#### `POST /api/ai/finalize-course-plan`
**Финализация плана курса в модули**

**Параметры:**
```json
{
  "session_id": "session_uuid",
  "user_id": "user_uuid", 
  "course_plan": "Детальный план курса...",
  "skill_area": "Python Programming",
  "track_id": "track_uuid"
}
```

**Ответ:**
```json
{
  "success": true,
  "modules_count": 5,
  "modules": [
    {
      "module_number": 1,
      "title": "Основы Python",
      "description": "Введение в синтаксис Python",
      "estimated_duration_hours": 8,
      "learning_objectives": ["Изучить переменные", "Понять циклы"],
      "status": "not_started"
    }
  ]
}
```

**Бизнес-логика:**
1. Генерация JSON модулей через OpenAI
2. Парсинг и валидация ответа
3. Создание записей `CourseModule` в БД
4. Сохранение AI сообщения в чат планирования

#### `POST /api/ai/chat-response`
**Обработка сообщения пользователя через AI**

**Параметры:**
```json
{
  "message": "Добавь модуль по тестированию",
  "session_id": "session_uuid",
  "track_context": "Python Programming Course"
}
```

#### `POST /api/ai/generate-lesson`
**Генерация контента урока**

#### `GET /api/ai/default-config`
**Получение конфигурации AI по умолчанию**

**Ответ:**
```json
{
  "model_name": "gpt-4o-mini",
  "base_url": "https://api.openai.com/v1",
  "has_custom_key": true
}
```

#### `POST /api/ai/test-connection`
**Тестирование подключения к AI**

**Параметры:**
```json
{
  "api_key": "sk-optional-test-key",
  "base_url": "https://api.openai.com/v1",
  "model_name": "gpt-4o-mini"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "✅ Подключение к OpenAI успешно!",
  "model_used": "gpt-4o-mini"
}
```

---

## 🔄 WebSocket Integration

### Основной WebSocket: `/ws/chat/{session_id}`

**Подключение:**
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/chat/${sessionId}`);
```

#### Восстановление истории чата
**Frontend → Backend:**
```json
{
  "type": "restore_chat",
  "user_id": "user_uuid"
}
```

**Backend → Frontend:**
```json
{
  "type": "chat_restored",
  "session_id": "session_uuid",
  "success": true,
  "has_existing_chat": true,
  "chat_id": "existing_chat_uuid",
  "chat_info": {
    "id": "chat_uuid",
    "chat_name": "Course Planning",
    "chat_type": "planning"
  },
  "history": [
    {
      "sender_type": "ai",
      "message_content": "Приветственное сообщение...",
      "timestamp": "2024-01-01T00:00:00Z",
      "tokens_used": 450,
      "ai_model_used": "gpt-4o-mini"
    }
  ],
  "message_count": 15,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Отправка сообщения пользователя
**Frontend → Backend:**
```json
{
  "message": "Добавь модуль по тестированию",
  "user_id": "user_uuid",
  "type": "text",
  "chat_id": "chat_uuid"
}
```

**Backend → Frontend:**
```json
{
  "type": "ai_response",
  "message": "Отличная идея! Добавлю модуль по тестированию...",
  "session_id": "session_uuid",
  "chat_id": "chat_uuid",
  "tokens_used": 200,
  "ai_model_used": "gpt-4o-mini",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Обработка ошибок
**Backend → Frontend:**
```json
{
  "type": "error",
  "message": "🚫 Произошла ошибка при обработке сообщения",
  "session_id": "session_uuid",
  "chat_id": "chat_uuid",
  "timestamp": null
}
```

### WebSocket для переключения чатов: `/ws/chat/{session_id}/switch`

**Команда переключения:**
```json
{
  "command": "switch_chat",
  "chat_id": "target_chat_uuid",
  "user_id": "user_uuid"
}
```

**Ответ:**
```json
{
  "type": "chat_switched",
  "chat_id": "target_chat_uuid",
  "history": [...],
  "message_count": 10
}
```

---

## 🧠 **LLM Workflow - Полный цикл работы с ИИ**

> **🔧 ИСПРАВЛЕНО:** Убрано дублирование генерации плана. Теперь план генерируется только в welcome-message.

### 📋 **Обновленный workflow планирования курса:**

#### **1️⃣ Создание трека** (`POST /api/tracks`)
```python
# routers/tracks.py -> create_track()
# ❌ УБРАНО: Автоматическая генерация AI плана 
# ✅ ИСПРАВЛЕНО: Создается только трек
new_track = LearningTrack(
    user_id=user_id,
    title=track_data.title,
    status=TrackStatus.PLANNING,
    ai_generated_plan=None  # ← Изначально пустой!
)
```

#### **2️⃣ Первая генерация плана** (`POST /api/ai/welcome-message`)
```python
# ✅ ЕДИНСТВЕННОЕ место генерации плана
# services/chat_service.py -> send_welcome_message()
chat_id = await self.create_or_get_chat(session_id, "Course Planning", "planning", db, user_id)
result = await openai_service.generate_welcome_plan_message(
    skill_area=skill_area,
    user_expectations=user_expectations,
    difficulty_level=difficulty_level,
    duration_hours=duration_hours
)
```

**💬 Что отправляется в LLM:**
```python
# services/openai_service.py -> generate_welcome_plan_message()
messages = [
    {
        "role": "system", 
        "content": f"""Ты - опытный ментор по обучению. Создай приветственное сообщение и детальный план курса:

📚 **Навык:** {skill_area}
🎯 **Уровень:** {difficulty_level}  
⏱️ **Длительность:** {duration_hours} часов
💭 **Ожидания:** {user_expectations}

Включи:
1. 👋 Приветствие и мотивацию
2. 📋 Структурированный план курса с модулями
3. 🎨 Эмодзи для наглядности
4. 💬 Приглашение к обсуждению и корректировкам

Формат: дружелюбное сообщение с четкой структурой курса."""
    },
    {"role": "user", "content": f"Создай план курса: {skill_area}"}
]
```

**🔄 Результат:** План сохраняется в единый чат планирования

#### **3️⃣ Диалог и корректировка** (WebSocket `/ws/chat/{session_id}`)
```python
# services/chat_service.py -> process_message()
# ✅ Получаем ВСЮ историю диалога + новое сообщение
chat_history = await self._get_chat_history(chat_id, db, limit=50)
messages = chat_history + [{"role": "user", "content": message}]

ai_result = await openai_service.generate_chat_response(
    messages=messages,  # ← Полная история планирования!
    context=track_context
)
```

**💬 Что отправляется в LLM на каждом шаге:**
```python
messages = [
    {"role": "assistant", "content": "🎯 Добро пожаловать! План курса: [детальный план]"},
    {"role": "user", "content": "Можешь добавить больше практических заданий?"},
    {"role": "assistant", "content": "Отлично! Обновленный план: [план с практикой]"},
    {"role": "user", "content": "А можно сократить модуль по теории?"},
    {"role": "assistant", "content": "Конечно! Финальная версия: [итоговый план]"},
    # ... вся эволюция плана через диалог
    {"role": "user", "content": "Последнее сообщение пользователя"}
]
```

**🔄 Особенности диалога:**
- Все обсуждение в **одном чате планирования**
- План **эволюционирует** через диалог
- LLM видит **полную историю** изменений
- Сохраняются все **промежуточные версии** планов

#### **4️⃣ Финализация плана** (`POST /api/ai/finalize-course-plan`)
```python
# ✅ ИСПРАВЛЕНО: Автоматическое извлечение плана из истории
# services/chat_service.py -> finalize_course_plan()

# 1. Извлекаем ПОСЛЕДНИЙ план из истории чата:
chat_history_db = await self._get_chat_history(chat_id, db, limit=50)
course_plan = ""
for msg in reversed(chat_history_db):
    if msg["role"] == "assistant":
        course_plan = msg["content"]  # ← Берем финальную версию!
        break

# 2. Генерируем структурированные модули:
result = await openai_service.generate_finalized_modules(course_plan, skill_area)
```

**💬 Что отправляется в LLM при финализации:**
```python
# services/openai_service.py -> generate_finalized_modules()
messages = [
    {
        "role": "system", 
        "content": """Ты - эксперт по структурированию образовательных программ.

🎯 **Задача:** Преобразовать текстовый план курса в JSON массив модулей.

📋 **Требования к каждому модулю:**
- title: название модуля (краткое и понятное)
- description: описание содержания модуля
- learning_objectives: массив конкретных целей обучения
- estimated_duration_hours: количество часов (реалистичное)

⚡ **ВАЖНО:** Верни ТОЛЬКО валидный JSON массив без дополнительных комментариев."""
    },
    {
        "role": "user", 
        "content": f"""Структурируй план курса по теме "{skill_area}" в JSON модули:

{course_plan}

Ответ: JSON массив модулей."""
    }
]
```

#### **5️⃣ Создание модулей в БД**
```python
# Парсим и сохраняем модули:
modules_data = json.loads(result["content"])

for i, module_data in enumerate(modules_data, 1):
    new_module = CourseModule(
        track_id=track_uuid,
        module_number=i,
        title=module_data.get("title"),
        description=module_data.get("description"),
        learning_objectives=module_data.get("learning_objectives", []),
        estimated_duration_hours=module_data.get("estimated_duration_hours", 5),
        ai_generated_content=module_data,
        status="not_started"
    )
    db.add(new_module)

# Обновляем статус трека:
track.status = TrackStatus.ACTIVE
```

---

### 🔄 **Исправленная диаграмма workflow:**

```mermaid
sequenceDiagram
    participant F as Frontend
    participant B as Backend
    participant CM as ChatManager  
    participant AI as OpenAI
    participant DB as Database

    Note over F,DB: 1️⃣ Создание трека (БЕЗ генерации плана)
    F->>B: POST /api/tracks (track data)
    B->>DB: Create learning track (ai_generated_plan = null)
    B-->>F: Track created

    Note over F,DB: 2️⃣ Генерация приветственного плана
    F->>B: POST /api/ai/welcome-message
    B->>CM: send_welcome_message()
    CM->>CM: create_or_get_chat("planning")
    CM->>AI: generate_welcome_plan_message()
    AI-->>CM: ✅ ПЕРВЫЙ план курса
    CM->>DB: Save AI message with plan
    CM-->>F: chat_id + welcome message

    Note over F,DB: 3️⃣ Диалог и корректировка плана
    F->>CM: WebSocket user message
    CM->>DB: Get FULL chat history
    CM->>AI: generate_chat_response(history + new_message)
    AI-->>CM: ✅ ОБНОВЛЕННЫЙ план
    CM->>DB: Save updated plan message
    CM-->>F: Real-time AI response

    Note over F,DB: 4️⃣ Финализация (автоматическое извлечение)
    F->>B: POST /api/ai/finalize-course-plan
    B->>CM: finalize_course_plan()
    CM->>DB: Get chat history
    CM->>CM: Extract LAST AI message (final plan)
    CM->>AI: generate_finalized_modules(final_plan)
    AI-->>CM: ✅ JSON modules array
    CM->>DB: Create CourseModule records
    CM-->>F: Modules created successfully
```

---

### 🎯 **Ключевые улучшения workflow:**

1. **❌ Убрано дублирование:** План генерируется только в welcome-message
2. **✅ Единый диалог:** Весь процесс планирования в одном чате  
3. **✅ Эволюция плана:** План развивается через естественный диалог
4. **✅ Автоматическое извлечение:** Финализация берет последний план из истории
5. **✅ Контекст сохраняется:** LLM видит всю историю изменений
6. **✅ Простота использования:** Frontend не передает course_plan вручную

---

### 🔧 **Промпты LLM по типам задач:**

#### **Welcome Message** (температура: 0.8)
```python
system_prompt = """Ты - дружелюбный AI-наставник по обучению. 
Создавай вдохновляющие планы курсов с четкой структурой и эмодзи."""

max_tokens = 1500
temperature = 0.8  # Для творческого подхода
```

#### **Chat Response** (температура: 0.7)  
```python
system_prompt = """Ты - помощник по планированию курсов.
Отвечай конструктивно, учитывая всю историю диалога."""

max_tokens = 1000  
temperature = 0.7  # Баланс творчества и точности
```

#### **Finalized Modules** (температура: 0.3)
```python
system_prompt = """Ты - эксперт по структурированию курсов.
Создавай только валидный JSON без комментариев."""

max_tokens = 2000
temperature = 0.3  # Для точности структуры
```

---

## 🏗️ Services Architecture

### ChatService (`services/chat_service.py`)

**Основной класс:** `ChatManager`

**Ключевые методы:**

#### Управление соединениями
```python
async def connect(websocket: WebSocket, session_id: str)
def disconnect(session_id: str)
async def send_message(session_id: str, message: dict)
```

#### Управление сессиями и чатами
```python
async def create_or_get_session(user_id, track_id, session_name, db) -> str
async def create_or_get_chat(session_id, chat_name, chat_type, db, user_id) -> str
async def restore_chat_history(session_id, chat_id, user_id, db) -> List[dict]
```

#### Обработка сообщений
```python
async def process_message(session_id, message, user_id, db, message_type, chat_id)
async def send_welcome_message(session_id, skill_area, user_expectations, ...)
async def finalize_course_plan(session_id, course_plan, skill_area, track_id, ...)
```

#### Восстановление диалогов
```python
async def restore_existing_chat_if_any(session_id, user_id, db) -> Dict
```

**Особенности реализации:**
- **Единый диалог планирования** - все сообщения в одном чате типа "planning"
- **Автоматическое восстановление** - при подключении к WebSocket
- **Изоляция чатов** - каждый чат имеет уникальный chat_id
- **Гостевая поддержка** - временные ID и in-memory хранение

### OpenAIService (`services/openai_service.py`)

**Основной класс:** `OpenAIService`

**Ключевые методы:**

#### Генерация контента
```python
async def generate_welcome_plan_message(skill_area, user_expectations, difficulty_level, duration_hours)
async def generate_course_plan(skill_area, user_expectations, difficulty_level, duration_hours)
async def generate_finalized_modules(course_plan, skill_area)
async def generate_chat_response(messages, context)
async def generate_lesson_content(lesson_title, module_context, content_type)
```

**Промпты и настройки:**
- **Температура**: 0.8 для творческих задач, 0.3 для структурированного JSON
- **Токены**: 1500-2000 для планов, 1000 для ответов
- **Система ролей**: Специализированные system prompts для каждой задачи

**Обработка ошибок:**
- Graceful fallback при недоступности API
- Retry логика для временных сбоев
- Fallback модули при ошибках парсинга JSON

---

## 🗄️ Database Models

### Иерархия данных
```
User
 └── LearningTrack
     ├── CourseModule[]
     └── ChatSession
         └── Chat (chat_id)
             └── ChatMessage[]
```

### Ключевые модели

#### ChatSession
```python
class ChatSession(Base):
    id = Column(UUID, primary_key=True)
    track_id = Column(UUID, ForeignKey("learning_tracks.id"))
    user_id = Column(UUID, ForeignKey("users.id"))
    session_name = Column(String(255))
    status = Column(String(20), default="active")
```

#### Chat
```python
class Chat(Base):
    id = Column(UUID, primary_key=True)  # chat_id
    session_id = Column(UUID, ForeignKey("chat_sessions.id"))
    chat_name = Column(String(255))
    chat_type = Column(String(50))  # planning, discussion, finalization
    status = Column(String(20), default="active")
    ai_context = Column(JSON)  # AI настройки для чата
```

#### ChatMessage
```python
class ChatMessage(Base):
    id = Column(UUID, primary_key=True)
    chat_id = Column(UUID, ForeignKey("chats.id"))  # Привязка к chat_id
    sender_type = Column(String(10))  # 'user' или 'ai'
    message_content = Column(Text)
    message_type = Column(String(50))  # 'text', 'welcome', 'finalization'
    ai_model_used = Column(String(100))  # 'gpt-4o-mini'
    tokens_used = Column(Integer)  # Для аналитики
    timestamp = Column(DateTime, default=datetime.utcnow)
```

#### CourseModule
```python
class CourseModule(Base):
    id = Column(UUID, primary_key=True)
    track_id = Column(UUID, ForeignKey("learning_tracks.id"))
    module_number = Column(Integer)
    title = Column(String(255))
    description = Column(Text)
    learning_objectives = Column(JSON)  # Массив целей
    estimated_duration_hours = Column(Integer)
    status = Column(String(50), default="not_started")
    ai_generated_content = Column(JSON)  # Дополнительный AI контент
```

---

## 🔧 Configuration & Environment

### Настройки (`utils/config.py`)

**Основные параметры:**
```python
class Settings(BaseSettings):
    # Приложение
    app_name: str = "AI Learning Platform"
    debug: bool = False
    
    # База данных
    database_url: str = "postgresql://user:password@localhost/ai_learning_platform"
    
    # Безопасность
    secret_key: str = "your-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI по умолчанию
    default_openai_api_key: Optional[str] = None
    default_openai_model: str = "gpt-3.5-turbo"
    default_openai_base_url: str = "https://api.openai.com/v1"
    
    # CORS
    allowed_origins: str = "http://localhost:3000,..."
```

**Переменные окружения (.env):**
```env
# Основные настройки
SECRET_KEY=your-secret-key-here
DEBUG=true

# База данных
DATABASE_URL=postgresql://user:password@localhost:5432/ai_learning_platform

# OpenAI API (ОБЯЗАТЕЛЬНО!)
DEFAULT_OPENAI_API_KEY=sk-your-real-openai-api-key-here
DEFAULT_OPENAI_MODEL=gpt-4o-mini
DEFAULT_OPENAI_BASE_URL=https://api.openai.com/v1

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

---

## 🚀 Frontend Integration Points

### Когда Frontend вызывает какие ручки

#### 1. **Вход пользователя**
```javascript
// Обычный пользователь
POST /api/auth/login → получение JWT токена

// Гостевой пользователь  
POST /api/auth/guest-login → получение гостевого токена
```

#### 2. **Создание трека**
```javascript
// 1. Создание трека (автоматически генерируется AI план)
POST /api/tracks → {title, description, skill_area, ...}

// 2. Создание сессии планирования
POST /api/chat/sessions → {track_id, session_name}

// 3. Автоматическое приветственное сообщение
POST /api/ai/welcome-message → {session_id, skill_area, ...}
// Результат: chat_id для дальнейшего использования
```

#### 3. **Открытие страницы трека**
```javascript
// 1. Получение трека с модулями
GET /api/tracks/{track_id}

// 2. Подключение к WebSocket
const ws = new WebSocket(`/ws/chat/${sessionId}`);

// 3. Автоматическое восстановление диалога
ws.send({type: "restore_chat", user_id: userId});
// Результат: полная история диалога планирования
```

#### 4. **Диалог с AI**
```javascript
// Через WebSocket
ws.send({
  message: "Добавь модуль по тестированию",
  user_id: userId,
  type: "text",
  chat_id: existingChatId
});

// Получение ответа в реальном времени
ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  // response.type === "ai_response"
  // response.message - ответ AI
  // response.tokens_used - использованные токены
};
```

#### 5. **Финализация плана курса**
```javascript
// Создание модулей из плана
POST /api/ai/finalize-course-plan → {
  session_id, 
  course_plan, 
  skill_area, 
  track_id
}
// Результат: модули созданы в БД, AI сообщение сохранено
```

#### 6. **Переключение между чатами**
```javascript
// Получение всех чатов пользователя
GET /api/chat/users/chats

// Переключение на конкретный чат
POST /api/chat/sessions/{session_id}/switch-chat → {chat_id}
// Результат: история выбранного чата
```

---

## 🎯 Development Best Practices

### Обработка ошибок
```python
# Graceful обработка AI ошибок
try:
    ai_response = await openai_service.generate_response(...)
    if ai_response["success"]:
        # Обработка успешного ответа
    else:
        # Fallback при ошибке AI
        logger.error(f"AI error: {ai_response['error']}")
except Exception as e:
    # Системная ошибка
    logger.error(f"System error: {str(e)}")
```

### Валидация данных
```python
# Проверка UUID
try:
    track_uuid = uuid.UUID(track_id)
except ValueError:
    raise HTTPException(status_code=400, detail="Invalid track ID format")

# Проверка прав доступа
if not current_user.email.startswith("guest_"):
    # Проверка через БД
```

### Логирование
```python
# Структурированное логирование
logger.info(f"Generated welcome message for {skill_area}, tokens: {tokens_used}")
logger.error(f"Failed to process message in session {session_id}: {str(e)}")
```

### Тестирование
```bash
# Тестирование WebSocket подключения
curl -X POST http://localhost:8000/api/ai/test-connection \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-test"}'

# Тестирование создания трека
curl -X POST http://localhost:8000/api/tracks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Track", "skill_area": "Python", ...}'
```

---

## 📊 Monitoring & Analytics

### Метрики для отслеживания
- **Использование токенов** по чатам и пользователям
- **Время отклика AI** для каждого типа запроса
- **Частота создания треков** и финализации планов
- **WebSocket соединения** и их длительность

### SQL запросы для аналитики
```sql
-- Использование токенов по типам чатов
SELECT 
    c.chat_type,
    COUNT(cm.id) as messages_count,
    SUM(cm.tokens_used) as total_tokens,
    AVG(cm.tokens_used) as avg_tokens
FROM chats c
JOIN chat_messages cm ON c.id = cm.chat_id
WHERE cm.sender_type = 'ai'
GROUP BY c.chat_type;

-- Активность пользователей в планировании
SELECT 
    u.email,
    COUNT(DISTINCT cs.id) as sessions_count,
    COUNT(DISTINCT c.id) as chats_count,
    SUM(cm.tokens_used) as total_tokens
FROM users u
JOIN chat_sessions cs ON u.id = cs.user_id
JOIN chats c ON cs.id = c.session_id
JOIN chat_messages cm ON c.id = cm.chat_id
WHERE c.chat_type = 'planning' AND cm.sender_type = 'ai'
GROUP BY u.id, u.email;
```

---

## 🔄 Data Flow Summary

### Полный цикл планирования курса

1. **Создание трека** → Автоматическая генерация AI плана
2. **Создание сессии** → Подготовка к планированию
3. **Приветственное сообщение** → AI предлагает детальный план
4. **Диалог планирования** → Уточнение и согласование плана
5. **Финализация** → Создание модулей курса в БД
6. **Восстановление** → Возврат к диалогу при повторном заходе

### Ключевые принципы
- **Единый чат** для всего процесса планирования
- **Изоляция LLM обращений** через chat_id  
- **Автоматическое восстановление** диалогов
- **Полная поддержка гостей** без потери функциональности
- **Детальная аналитика** использования AI

---

> **🎊 Backend готов к использованию!** Система поддерживает полный цикл планирования курсов с AI, включая гостевой режим, восстановление диалогов и детальную аналитику. 

### 📝 **Детальные примеры промптов и ответов LLM:**

#### **🎯 Welcome Message - Пример промпта:**
```python
# Входные данные:
skill_area = "Python для анализа данных"
difficulty_level = "intermediate" 
duration_hours = 40
user_expectations = "Хочу научиться анализировать данные и строить визуализации"

# Промпт в LLM:
{
  "role": "system",
  "content": """Ты - опытный ментор по обучению. Создай приветственное сообщение и детальный план курса:

📚 **Навык:** Python для анализа данных
🎯 **Уровень:** intermediate  
⏱️ **Длительность:** 40 часов
💭 **Ожидания:** Хочу научиться анализировать данные и строить визуализации

Включи:
1. 👋 Приветствие и мотивацию
2. 📋 Структурированный план курса с модулями
3. 🎨 Эмодзи для наглядности
4. 💬 Приглашение к обсуждению и корректировкам

Формат: дружелюбное сообщение с четкой структурой курса."""
},
{
  "role": "user", 
  "content": "Создай план курса: Python для анализа данных"
}
```

#### **💬 Welcome Message - Пример ответа LLM:**
```markdown
🎯 **Добро пожаловать в курс "Python для анализа данных"!**

Привет! Я твой AI-помощник по изучению анализа данных. Здорово, что ты решил освоить эту востребованную область! 🚀

## 📚 **План курса (40 часов):**

### **Модуль 1: Основы Python для данных** (8 часов)
- 🐍 Синтаксис Python и структуры данных
- 📊 Работа с NumPy массивами
- 🧮 Основы Pandas для работы с таблицами

### **Модуль 2: Загрузка и очистка данных** (10 часов)  
- 📁 Чтение файлов (CSV, Excel, JSON)
- 🧹 Очистка и предобработка данных
- 🔄 Работа с пропущенными значениями

### **Модуль 3: Анализ и статистика** (12 часов)
- 📈 Описательная статистика
- 🔍 Корреляционный анализ
- 📊 Группировка и агрегация данных

### **Модуль 4: Визуализация данных** (10 часов)
- 📊 Matplotlib: базовые графики
- 🎨 Seaborn: красивые визуализации
- 📈 Интерактивные графики с Plotly

---

💬 **Что думаешь о таком плане?** Хочешь изменить акценты, добавить больше практики или углубиться в какую-то область?
```

#### **🔄 Chat Response - Пример диалога:**
```python
# История диалога + новое сообщение:
messages = [
    {"role": "assistant", "content": "[приветственное сообщение выше]"},
    {"role": "user", "content": "Отлично! Можешь добавить модуль по машинному обучению?"},
    {"role": "assistant", "content": "Замечательная идея! ML отлично дополнит анализ данных..."},
    {"role": "user", "content": "А можно сделать больше практических проектов?"}
]

# Ответ LLM:
```

```markdown
🎯 **Отличное предложение!** Практика - основа обучения. Обновляю план:

## 📚 **Обновленный план курса (40 часов):**

### **Модуль 1: Python для данных + Проект** (8 часов)
- 🐍 Основы Python, NumPy, Pandas
- 🏗️ **Проект:** Анализ продаж интернет-магазина

### **Модуль 2: Данные + Проект** (10 часов)  
- 📁 Загрузка, очистка, предобработка
- 🏗️ **Проект:** Очистка реального датасета с вакансиями

### **Модуль 3: Анализ + Проект** (10 часов)
- 📈 Статистика, корреляции, инсайты  
- 🏗️ **Проект:** Исследование рынка недвижимости

### **Модуль 4: Визуализация + Проект** (8 часов)
- 📊 Matplotlib, Seaborn, Plotly
- 🏗️ **Проект:** Дашборд для бизнес-аналитики

### **Модуль 5: Машинное обучение + Итоговый проект** (4 часа)
- 🤖 Scikit-learn: регрессия, классификация
- 🏆 **Финальный проект:** Предсказание цен или категорий

---

💡 **Теперь 80% времени - практика!** Каждый модуль завершается реальным проектом для портфолио.
```

#### **🎯 Finalize Modules - Пример промпта:**
```python
# Промпт для структурирования:
{
  "role": "system",
  "content": """Ты - эксперт по структурированию образовательных программ.

🎯 **Задача:** Преобразовать текстовый план курса в JSON массив модулей.

📋 **Требования к каждому модулю:**
- title: название модуля (краткое и понятное)
- description: описание содержания модуля
- learning_objectives: массив конкретных целей обучения
- estimated_duration_hours: количество часов (реалистичное)

⚡ **ВАЖНО:** Верни ТОЛЬКО валидный JSON массив без дополнительных комментариев."""
},
{
  "role": "user",
  "content": """Структурируй план курса по теме "Python для анализа данных" в JSON модули:

[весь финальный план из диалога выше]

Ответ: JSON массив модулей."""
}
```

#### **📋 Finalize Modules - Пример ответа LLM:**
```json
[
  {
    "title": "Python для данных + Проект",
    "description": "Освоение основ Python, работа с NumPy и Pandas, создание первого аналитического проекта",
    "learning_objectives": [
      "Освоить синтаксис Python для анализа данных",
      "Научиться работать с NumPy массивами", 
      "Изучить основы библиотеки Pandas",
      "Создать проект анализа продаж интернет-магазина"
    ],
    "estimated_duration_hours": 8
  },
  {
    "title": "Загрузка и очистка данных + Проект", 
    "description": "Работа с различными форматами данных, методы очистки и предобработки, практический проект",
    "learning_objectives": [
      "Загружать данные из CSV, Excel, JSON",
      "Очищать и предобрабатывать реальные датасеты",
      "Работать с пропущенными значениями",
      "Применить навыки на датасете с вакансиями"
    ],
    "estimated_duration_hours": 10
  },
  {
    "title": "Статистический анализ + Проект",
    "description": "Описательная статистика, корреляционный анализ, извлечение инсайтов из данных",
    "learning_objectives": [
      "Вычислять описательную статистику",
      "Проводить корреляционный анализ", 
      "Группировать и агрегировать данные",
      "Исследовать рынок недвижимости"
    ],
    "estimated_duration_hours": 10
  },
  {
    "title": "Визуализация данных + Проект",
    "description": "Создание информативных графиков с помощью Matplotlib, Seaborn и Plotly",
    "learning_objectives": [
      "Строить графики с Matplotlib",
      "Создавать красивые визуализации с Seaborn",
      "Делать интерактивные графики с Plotly",
      "Разработать бизнес-дашборд"
    ],
    "estimated_duration_hours": 8
  },
  {
    "title": "Машинное обучение + Итоговый проект", 
    "description": "Основы ML с Scikit-learn, создание финального проекта для портфолио",
    "learning_objectives": [
      "Понять принципы машинного обучения",
      "Применить регрессию и классификацию",
      "Оценить качество моделей",
      "Создать итоговый проект-предсказание"
    ],
    "estimated_duration_hours": 4
  }
]
```

---

### 🔍 **Мониторинг использования LLM:**

#### **Метрики по токенам:**
```sql
-- Использование токенов по этапам планирования
SELECT 
    CASE 
        WHEN cm.message_content LIKE '%Добро пожаловать%' THEN 'Welcome'
        WHEN EXISTS(SELECT 1 FROM chat_messages cm2 
                   WHERE cm2.chat_id = cm.chat_id 
                   AND cm2.id < cm.id 
                   AND cm2.sender_type = 'ai') THEN 'Discussion'
        ELSE 'Other'
    END as stage,
    COUNT(*) as messages_count,
    AVG(cm.tokens_used) as avg_tokens,
    SUM(cm.tokens_used) as total_tokens
FROM chat_messages cm 
WHERE cm.sender_type = 'ai' AND cm.tokens_used IS NOT NULL
GROUP BY stage;
```

#### **Качество планирования:**
```sql  
-- Треки с успешной финализацией
SELECT 
    t.skill_area,
    COUNT(t.id) as tracks_created,
    COUNT(cm.id) as tracks_with_modules,
    ROUND(COUNT(cm.id) * 100.0 / COUNT(t.id), 2) as success_rate
FROM learning_tracks t
LEFT JOIN course_modules cm ON t.id = cm.track_id
WHERE t.created_at >= '2024-01-01'
GROUP BY t.skill_area
ORDER BY success_rate DESC;
```

--- 