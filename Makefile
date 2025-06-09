.PHONY: help up down logs init-backend

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  up              - Start services in detached mode"
	@echo "  down            - Stop and remove services"
	@echo "  logs            - View logs from services"
	@echo "  init-backend    - Create backend directory structure"


up:
	@echo "Starting up services (PostgreSQL & Redis)..."
	@docker compose up -d
	@echo "Services are up and running."

down:
	@echo "Stopping services..."
	@docker-compose down --remove-orphans
	@echo "Services stopped."

logs:
	@echo "Showing logs for all services..."
	@docker-compose logs -f

init-backend:
	@echo "Initializing backend directory structure..."
	@mkdir -p backend/src/api backend/src/services/auth backend/src/services/users backend/src/services/courses backend/src/services/chat/agents backend/src/services/chat/memory backend/src/services/chat/tools backend/src/core backend/src/config backend/tests
	@touch backend/src/api/__init__.py
	@touch backend/src/services/__init__.py
	@touch backend/src/services/auth/__init__.py
	@touch backend/src/services/users/__init__.py
	@touch backend/src/services/courses/__init__.py
	@touch backend/src/services/chat/__init__.py
	@touch backend/src/services/chat/agents/__init__.py
	@touch backend/src/services/chat/memory/__init__.py
	@touch backend/src/services/chat/tools/__init__.py
	@touch backend/src/core/__init__.py
	@touch backend/src/config/__init__.py
	@touch backend/tests/__init__.py
	@touch backend/.env.example
	@touch backend/requirements.txt
	@echo "Backend structure initialized." 