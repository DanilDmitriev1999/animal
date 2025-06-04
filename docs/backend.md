# Backend Onboarding

Этот документ поможет быстро запустить и начать разработку серверной части AI Learning Platform.

## Требования
- Python 3.8+
- PostgreSQL (в контейнере Docker) 
- OpenAI API ключ

## Установка
1. Скопируйте `env.example` в `.env` и заполните значения.
2. Установите Python‑зависимости:
   ```bash
   make install
   ```
3. Запустите базу данных в Docker:
   ```bash
   make db-up
   ```
4. Создайте таблицы:
   ```bash
   make create-tables
   ```

## Запуск в разработке
Сервер запускается командой:
```bash
make dev
```
После запуска API будет доступно на `http://localhost:8000`, документация — на `/docs`.

## Структура проекта
- `main.py` – точка входа, настройка FastAPI и WebSocket.
- `routers/` – REST и WebSocket endpoints.
- `services/` – бизнес‑логика и интеграция с OpenAI.
- `models/` – SQLAlchemy модели и подключение к базе.
- `utils/config.py` – конфигурация и переменные окружения.

## Полезные команды
- `make stop-all` – остановить приложения и БД.
- `make db-reset` – пересоздать базу данных (удаляет данные!).

Подробнее о структуре API смотрите код роутеров в каталоге `routers`.

## Основные методы API

### Аутентификация (`/api/auth`)
- `POST /register` – регистрация нового пользователя. Тело запроса: `email`, `password`, `first_name`, `last_name`.
- `POST /login` – получение JWT токена по логину и паролю.
- `POST /guest-login` – вход гостя без создания аккаунта.
- `GET /me` – данные текущего пользователя по заголовку `Authorization`.

### Учебные треки (`/api/tracks`)
- `GET /` – список треков текущего пользователя.
- `POST /` – создание трека (`title`, `description`, `skill_area`, `difficulty_level`, `estimated_duration_hours`, `user_expectations`).
- `GET /{track_id}` – подробная информация о треке и его модулях.
- `PUT /{track_id}` – обновление трека.
- `DELETE /{track_id}` – удаление трека вместе с чатами и модулями.

### Планирование и чаты (`/api/chat`)
- `POST /sessions` – создать чат‑сессию для трека.
- `POST /chats` – создать чат внутри сессии.
- `GET /sessions/{session_id}/chats` – список чатов сессии.
- `GET /chats/{chat_id}/messages` – сообщения выбранного чата.
- `GET /sessions` – все сессии пользователя.
- `PUT /sessions/{session_id}/status` – изменить статус сессии (только для зарегистрированных).
- `PUT /chats/{chat_id}/status` – изменить статус чата.

### AI сервис (`/api/ai`)
- `POST /generate-plan` – генерация плана курса по введённым параметрам. Может
  принимать `session_id` и `chat_id` для учёта истории диалога.
- `POST /chat-response` – ответ AI в чате планирования. Принимает `chat_id`
  (опционально) и возвращает тот же идентификатор для продолжения диалога.
- `POST /generate-lesson` – генерация материалов урока.
- `GET /user-config` – параметры AI пользователя.
- `GET /default-config` – конфигурация AI по умолчанию.
- `POST /test-connection` – проверка соединения с OpenAI.
- `POST /welcome-message` – приветствие и предварительный план.
- `POST /finalize-course-plan` – финализация плана и создание модулей.
- `POST /module-learning-start` – старт изучения модуля и создание чата.
- `POST /module-chat` – отправка сообщения в чат модуля.
- `POST /module-complete` – завершение модуля.
- `POST /module-chat-history` – история чата модуля.

### WebSocket
- `/ws/chat/{session_id}` – основной канал общения при планировании.
- `/ws/chat/{session_id}/switch` – переключение между чатами и восстановление истории.

## Взаимодействие с фронтендом
Фронтенд обращается к REST API для регистрации пользователей, управления треками и получения данных. Для диалогов используется WebSocket. В режиме разработки Vite проксирует запросы `/api/*` на порт 8000.

