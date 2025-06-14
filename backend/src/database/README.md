# База данных AI Learning Platform

Этот модуль содержит все файлы для работы с базой данных PostgreSQL.

## 📁 Структура файлов

- **`init_db.sql`** - SQL скрипт для создания таблиц и начальных данных
- **`db_init.py`** - Python скрипт для инициализации БД
- **`config.py`** - Конфигурация SQLAlchemy и подключения к БД  
- **`test_data.py`** - Тестирование работы с данными

## 🗄️ Схема базы данных

### Основные таблицы:

1. **`users`** - Пользователи системы
   - Аутентификация (email, password_hash)
   - Профиль (имя, роль, AI-стиль)
   - Метаданные (даты создания, последнего входа)

2. **`tracks`** - Учебные треки (курсы)
   - Основная информация (название, описание, изображение)
   - Характеристики (сложность, продолжительность)
   - Статус публикации

3. **`modules`** - Модули внутри треков
   - Связь с треком
   - Порядок следования (order_index)

4. **`lessons`** - Уроки внутри модулей
   - Связь с модулем
   - Тип урока (theory, practice, quiz, project)
   - Контент и метаданные

5. **`user_progress`** - Прогресс пользователей
   - Связь пользователь-урок
   - Процент выполнения и время
   - Статус завершения

6. **`chat_messages`** - История чатов с AI
   - Связь с пользователем
   - Тип агента (dashboard, course)
   - Контекст (JSONB с метаданными)
   - Роль и содержимое сообщения

## 🚀 Быстрый старт

### 1. Запуск инфраструктуры:
```bash
# Из корня проекта
make up
```

### 2. Инициализация БД:
```bash
source venv/bin/activate
python backend/src/database/db_init.py
```

### 3. Тестирование:
```bash
python backend/src/database/test_data.py
```

## 🔧 Конфигурация

Параметры подключения настраиваются через переменные окружения:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_learning_db
DB_USER=user
DB_PASSWORD=password
```

По умолчанию используются значения из `docker-compose.yml`.

## 🧪 Тестовые данные

После инициализации доступны:

- **Пользователь**: `test@example.com` / `test123`
- **Треки**: Основы Python, Машинное обучение, Веб-разработка
- **Модули и уроки** для каждого трека
- **Образцы чатов** и прогресса

## 📚 Использование в коде

```python
from database.config import get_db_session, engine

# Для FastAPI routes
@app.get("/users")
def get_users(db: Session = Depends(get_db_session)):
    return db.query(User).all()

# Для standalone скриптов
from database.config import SessionLocal
db = SessionLocal()
users = db.query(User).all()
db.close()
``` 