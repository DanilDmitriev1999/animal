# AI Learning Platform - Makefile

.PHONY: help install setup-env db-up db-down dev clean test frontend-install frontend-dev frontend-build

help: ## Показать помощь
	@echo "AI Learning Platform - Команды управления"
	@echo ""
	@echo "Использование: make [команда]"
	@echo ""
	@echo "Backend команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Установить зависимости Python (backend)
	pip install -r requirements.txt

frontend-install: ## Установить зависимости Node.js (frontend)
	cd frontend && npm install

setup-env: ## Создать .env файл из примера
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "✅ Файл .env создан из env.example"; \
		echo "🔧 Настройте переменные окружения в файле .env"; \
	else \
		echo "⚠️  Файл .env уже существует"; \
	fi

db-up: ## Запустить PostgreSQL через Docker
	docker compose up -d db
	@echo "⏳ Ждем запуска базы данных..."
	@sleep 10
	@echo "✅ PostgreSQL запущен на порту 5432"
	@echo "📊 Данные для подключения:"
	@echo "   Host: localhost:5432"
	@echo "   Database: ai_learning_platform"
	@echo "   User: user"
	@echo "   Password: password"

db-down: ## Остановить PostgreSQL
	docker compose down
	@echo "✅ PostgreSQL остановлен"

dev: ## Запустить FastAPI backend сервер
	@echo "🚀 Запуск AI Learning Platform Backend..."
	@echo "📡 API сервер: http://localhost:8000"
	@echo "📚 API документация: http://localhost:8000/docs"
	@echo "⚠️  Для запуска frontend используйте: make frontend-dev"
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend-dev: ## Запустить Vite frontend сервер
	@echo "🌐 Запуск AI Learning Platform Frontend..."
	@echo "🖥️  Frontend: http://localhost:3000"
	@echo "⚠️  Убедитесь, что backend запущен: make dev"
	cd frontend && npm run dev

frontend-build: ## Собрать frontend для продакшена
	@echo "🏗️  Сборка frontend..."
	cd frontend && npm run build
	@echo "✅ Frontend собран в frontend/dist/"

create-tables: ## Создать таблицы в базе данных
	python -c "from models.database import create_tables; import asyncio; asyncio.run(create_tables())"

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	cd frontend && rm -rf dist node_modules/.vite

migrate-chat-id: ## Мигрировать существующую БД к структуре с chat_id
	@echo "🔄 Запуск миграции к chat_id..."
	docker exec -i ai-learning-platform-db-1 psql -U user -d ai_learning_platform < migrate_to_chat_id.sql
	@echo "✅ Миграция завершена!"

migrate: ## Запустить миграции (если есть)
	$(MAKE) migrate-chat-id

stop-all: ## Остановить все сервисы
	@echo "🛑 Остановка всех сервисов..."
	@-pkill -f "uvicorn main:app" 2>/dev/null || true
	@-pkill -f "npm run dev" 2>/dev/null || true
	@-pkill -f "vite" 2>/dev/null || true
	docker compose down
	@echo "✅ Все сервисы остановлены"

db-reset-force: ## Пересоздать БД без подтверждения (ОСТОРОЖНО!)
	@echo "🗑️  Принудительное пересоздание БД..."
	docker compose down -v
	docker volume prune -f
	$(MAKE) db-up
	$(MAKE) create-tables
	@echo "✅ БД пересоздана"

setup-new-env: ## Создать .env с настройками для chat_id архитектуры
	@echo "🔧 Создание .env для новой архитектуры..."
	@echo "# AI Learning Platform - Chat ID архитектура" > .env
	@echo "SECRET_KEY=your-secret-key-change-in-production" >> .env
	@echo "DEBUG=true" >> .env
	@echo "" >> .env
	@echo "# База данных" >> .env
	@echo "DATABASE_URL=postgresql://user:password@localhost:5432/ai_learning_platform" >> .env
	@echo "" >> .env
	@echo "# 🤖 OpenAI API (ОБЯЗАТЕЛЬНО!)" >> .env
	@echo "DEFAULT_OPENAI_API_KEY=sk-your-real-openai-api-key-here" >> .env
	@echo "DEFAULT_OPENAI_MODEL=gpt-4o-mini" >> .env
	@echo "DEFAULT_OPENAI_BASE_URL=https://api.openai.com/v1" >> .env
	@echo "" >> .env
	@echo "# JWT настройки" >> .env
	@echo "ACCESS_TOKEN_EXPIRE_MINUTES=30" >> .env
	@echo "ALGORITHM=HS256" >> .env
	@echo "" >> .env
	@echo "# CORS для разработки" >> .env
	@echo 'CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]' >> .env
	@echo "✅ Файл .env создан"
	@echo "🔑 ВАЖНО: Установите ваш OpenAI API ключ в DEFAULT_OPENAI_API_KEY"

full-setup-new: ## Полная настройка с новой chat_id архитектурой
	@echo "🚀 Полная настройка с chat_id архитектурой..."
	$(MAKE) setup-new-env
	$(MAKE) frontend-install
	$(MAKE) install
	$(MAKE) db-reset-force
	@echo ""
	@echo "🎉 Настройка завершена!"
	@echo ""
	@echo "📝 Следующие шаги:"
	@echo "1. Установите OpenAI API ключ в .env файле"
	@echo "2. Запустите приложение:"
	@echo "   make dev       # Backend"
	@echo "   make frontend-dev  # Frontend"
	@echo ""
	@echo "🌐 После запуска:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API docs: http://localhost:8000/docs" 