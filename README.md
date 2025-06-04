# AI Learning Platform

Веб‑приложение для планирования и прохождения учебных курсов с помощью искусственного интеллекта.

## Быстрый старт
1. Скопируйте `env.example` в `.env` и укажите ключ OpenAI.
2. Установите зависимости и запустите базу данных:
   ```bash
   make install
   make frontend-install
   make db-up
   make create-tables
   ```
3. Запустите приложение в двух терминалах:
   ```bash
   make dev           # backend на http://localhost:8000
   make frontend-dev  # frontend на http://localhost:3000
   ```

## Структура репозитория
- `main.py` и `routers/` – FastAPI backend
- `frontend/` – Vite + vanilla JS SPA
- `models/` – SQLAlchemy модели
- `services/` – логика работы с AI и чатами
- `docs/` – onboarding‑документация

## Дополнительная информация
Подробные инструкции по разработке находятся в:
- [docs/backend.md](docs/backend.md)
- [docs/frontend.md](docs/frontend.md)
- [docs/database.md](docs/database.md)
\nGuest chat history is stored in guest_history.json for session recovery.
