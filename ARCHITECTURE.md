# 🏗️ Архитектура AI Learning Platform

## Обзор

AI Learning Platform представляет собой полноценное веб-приложение для персонализированного обучения с использованием искусственного интеллекта. Архитектура состоит из двух основных компонентов:

- **Frontend**: Single Page Application (SPA) на чистом JavaScript
- **Backend**: FastAPI REST API с поддержкой WebSocket

## 📁 Структура проекта

```
ai-learning-platform/
├── 📁 static/                    # Frontend (SPA)
│   ├── 🌐 index.html            # Единая HTML страница
│   ├── ⚡ app.js                # JavaScript логика приложения  
│   └── 🎨 style.css             # Стили и анимации
│
├── 📁 models/                    # Модели данных
│   ├── 🗄️ database.py           # Подключение к БД
│   └── 📊 database_models.py    # SQLAlchemy модели
│
├── 📁 routers/                   # API endpoints
│   ├── 🔐 auth.py               # Аутентификация
│   ├── 📚 tracks.py             # Учебные треки
│   ├── 💬 chat.py               # Чат планирования
│   └── 🤖 ai_service.py         # AI сервис
│
├── 📁 services/                  # Бизнес-логика
│   ├── 💬 chat_service.py       # WebSocket чат
│   └── 🤖 openai_service.py     # OpenAI интеграция
│
├── 📁 utils/                     # Утилиты
│   └── ⚙️ config.py             # Конфигурация
│
├── 🚀 main.py                   # FastAPI приложение
├── 🐳 docker-compose.yml        # Docker настройки
├── 🗄️ init.sql                 # Инициализация БД
├── 📋 requirements.txt          # Python зависимости
└── 🛠️ Makefile                 # Команды управления
```

## 🌐 Frontend Architecture

### Технологии
- **Vanilla JavaScript** - нет зависимостей от фреймворков
- **HTML5** - семантическая разметка
- **CSS3** - современные стили с анимациями
- **Local Storage** - локальное хранение данных
- **WebSocket API** - real-time коммуникация

### Основные компоненты

#### 1. Landing Page
- Посадочная страница с описанием платформы
- Hero секция с призывом к действию
- Карточки с преимуществами обучения

#### 2. Authentication
- Формы входа и регистрации
- Клиентская валидация
- Переключение между режимами

#### 3. Dashboard
- Sidebar навигация
- Список треков обучения
- Профиль пользователя
- Настройки AI

#### 4. Track Management
- Создание новых треков
- Планирование с AI
- Real-time чат интерфейс

### API Integration
```javascript
// Конфигурация API
const API_ENDPOINTS = {
    auth: {
        register: '/api/auth/register',
        login: '/api/auth/login'
    },
    tracks: {
        list: '/api/tracks',
        create: '/api/tracks'
    },
    chat: {
        websocket: (sessionId) => `ws://localhost:8000/ws/chat/${sessionId}`
    }
};

// Универсальная функция API запросов
async function apiRequest(endpoint, options = {}) {
    // JWT токен автоматически добавляется
    // Обработка ошибок
    // JSON сериализация/десериализация
}
```

## 🔧 Backend Architecture

### Технологии
- **FastAPI** - современный Python веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **PostgreSQL** - основная база данных
- **asyncpg** - асинхронный драйвер PostgreSQL
- **WebSocket** - real-time коммуникация
- **JWT** - аутентификация

### Модели данных

#### User Model
```python
class User(Base):
    id = Column(UUID, primary_key=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(Enum(UserRole))
```

#### Learning Track Model
```python
class LearningTrack(Base):
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    title = Column(String)
    description = Column(Text)
    difficulty_level = Column(Enum(DifficultyLevel))
    ai_generated_plan = Column(JSON)
```

### API Endpoints

#### Authentication
```
POST /api/auth/register    # Регистрация
POST /api/auth/login       # Вход
GET  /api/auth/me          # Текущий пользователь
```

#### Learning Tracks
```
GET    /api/tracks         # Список треков
POST   /api/tracks         # Создание трека
GET    /api/tracks/{id}    # Детали трека
PUT    /api/tracks/{id}    # Обновление трека
```

#### Chat & AI
```
POST /api/chat/sessions              # Создание чат-сессии
GET  /api/chat/sessions/{id}/messages # История сообщений
WS   /ws/chat/{session_id}           # WebSocket чат
POST /api/ai/generate-plan           # Генерация плана
```

### WebSocket Chat Manager
```python
class ChatManager:
    def __init__(self):
        self.active_connections = {}
    
    async def connect(self, websocket, session_id):
        # Управление подключениями
    
    async def process_message(self, session_id, message, user_id):
        # Обработка сообщений через AI
```

## 🗄️ База данных

### PostgreSQL Schema
```sql
-- Основные таблицы
users                 # Пользователи
ai_configurations     # Настройки AI
learning_tracks       # Учебные треки
chat_sessions         # Сессии планирования
chat_messages         # Сообщения чата
course_modules        # Модули курсов
lessons               # Уроки
homework_assignments  # Домашние задания
```

### Связи между таблицами
- User → AI Configuration (1:1)
- User → Learning Tracks (1:N)
- Learning Track → Chat Sessions (1:N)
- Chat Session → Messages (1:N)
- Learning Track → Course Modules (1:N)
- Course Module → Lessons (1:N)

## 🔄 Data Flow

### 1. Аутентификация
```
Frontend → POST /api/auth/login → Backend → Database → JWT Token → Frontend
```

### 2. Создание трека
```
Frontend → POST /api/tracks → Backend → Database → Track Created → Frontend
```

### 3. AI Chat Planning
```
Frontend → WebSocket Connection → Chat Manager → AI Service → OpenAI API → Response → Frontend
```

## 🚀 Deployment

### Development
```bash
make full-setup  # Полная настройка
make dev         # Запуск в режиме разработки
```

### Production готовность
- ✅ Статические файлы служатся через FastAPI
- ✅ PostgreSQL в Docker контейнере
- ✅ Переменные окружения для конфигурации
- ✅ Логирование и мониторинг
- ✅ CORS настройки
- ✅ JWT аутентификация

### Масштабирование
- **Горизонтальное**: несколько инстансов FastAPI
- **Кэширование**: Redis для сессий и частых запросов
- **CDN**: для статических файлов
- **Load Balancer**: nginx для распределения нагрузки

## 🔧 Конфигурация

### Environment Variables
```env
DATABASE_URL=postgresql://user:password@localhost/ai_learning_platform
SECRET_KEY=your-secret-key
DEFAULT_OPENAI_API_KEY=your-openai-key
DEBUG=false
```

### Docker Services
```yaml
services:
  db:          # PostgreSQL database
  pgadmin:     # Database management (optional)
```

## 🔒 Безопасность

### Authentication & Authorization
- JWT токены для API доступа
- Хэширование паролей с bcrypt
- Шифрование API ключей в БД

### CORS
- Настроенные разрешенные origins
- Поддержка credentials для WebSocket

### Валидация
- Pydantic модели для валидации входных данных
- SQL injection защита через SQLAlchemy
- XSS защита через правильное экранирование

## 📊 Мониторинг

### Логирование
```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Health Check
```
GET /api/health  # Статус приложения
```

### Метрики
- Количество активных пользователей
- Созданные треки
- AI запросы
- WebSocket соединения

## 🔮 Будущие улучшения

### Техническая сторона
- [ ] Кэширование с Redis
- [ ] Очереди задач с Celery
- [ ] Тестирование (pytest)
- [ ] CI/CD pipeline
- [ ] Docker production setup

### Функциональность
- [ ] Уведомления
- [ ] Файловые вложения
- [ ] Экспорт данных
- [ ] Мобильное приложение
- [ ] Социальные функции 