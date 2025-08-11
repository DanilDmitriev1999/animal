.PHONY: help up down logs backend frontend db-reset db-schema db-seed db-init api worker

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  up              - Start services in detached mode"
	@echo "  down            - Stop and remove services"
	@echo "  logs            - View logs from services"
	@echo "  backend         - Run FastAPI server"
	@echo "  frontend        - Run Vite dev server"

up:
	@echo "Starting up services (PostgreSQL & Redis)"
	@docker compose up -d
	@echo "Services are up and running."

down:
	@echo "Stopping services..."
	@docker-compose down --remove-orphans
	@echo "Services stopped."

logs:
	@echo "Showing logs for all services..."
	@docker-compose logs -f

backend:
	@echo "Starting backend on http://localhost:8000"
 
api:
	@echo "Starting FastAPI on http://localhost:8000"
	@$(VENV_BIN)/uvicorn backend.app.main:app --reload --port 8000

frontend:
	@echo "Starting frontend on http://localhost:3000"
	@npm --prefix frontend run dev

worker:
	@echo "Starting agents RQ worker"
	@AGENT_WORKER_SIMPLE=1 $(VENV_BIN)/python -m backend.worker.run | cat
# AICODE-NOTE: AGENT_WORKER_SIMPLE=1 — используем простой воркер, который не использует Redis. Проблема из-за мака.

# AICODE-NOTE: DB helpers now use Python script backend/scripts/db.py (psycopg2)
# AICODE-NOTE: Virtualenv-aware: by default we use ./venv from project root
VENV_BIN ?= ./venv/bin
PYTHON ?= $(VENV_BIN)/python
PIP ?= $(VENV_BIN)/pip
DB_URL=postgresql://user:password@localhost:5432/ai_learning_db

db-reset:
	@echo "Reset database via Python ($(PYTHON))"
	@DB_URL=$(DB_URL) $(PYTHON) backend/scripts/db.py reset | cat

db-schema:
	@echo "Apply schema via Python ($(PYTHON))"
	@DB_URL=$(DB_URL) $(PYTHON) backend/scripts/db.py schema | cat

db-seed:
	@echo "Seed data via Python ($(PYTHON))"
	@DB_URL=$(DB_URL) $(PYTHON) backend/scripts/db.py seed | cat

db-init:
	@echo "Init database (reset + schema + seed) via Python ($(PYTHON))"
	@DB_URL=$(DB_URL) $(PYTHON) backend/scripts/db.py init | cat
