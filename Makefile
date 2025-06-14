.PHONY: help up down logs init-backend

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  up              - Start services in detached mode"
	@echo "  down            - Stop and remove services"
	@echo "  logs            - View logs from services"

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

