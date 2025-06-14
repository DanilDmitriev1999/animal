.PHONY: help up down logs backend frontend

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
	@PYTHONPATH=backend/src uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "Starting frontend on http://localhost:3000"
	@npm --prefix frontend run dev

