.PHONY: help up down logs seed test lint build clean

help:
	@echo "GymOS Enterprise — Development Commands"
	@echo ""
	@echo "  make up        Start all services (Docker)"
	@echo "  make down      Stop all services"
	@echo "  make seed      Seed database with initial data"
	@echo "  make test      Run backend test suite"
	@echo "  make lint      Run linters (ruff)"
	@echo "  make build     Build frontend for production"
	@echo "  make logs      Tail all service logs"
	@echo "  make clean     Remove containers and volumes"
	@echo "  make migrate   Run Alembic migrations"
	@echo "  make shell     Open backend Python shell"

up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up -d
	@echo "✓ Services started"
	@echo "  Frontend: http://localhost:5173"
	@echo "  API:      http://localhost:8000/api/docs"

down:
	docker compose down

logs:
	docker compose logs -f

seed:
	docker compose exec backend python app/utils/seed.py

migrate:
	docker compose exec backend alembic upgrade head

test:
	cd backend && pip install -r requirements.txt -q && pytest

lint:
	cd backend && pip install ruff -q && ruff check app/
	cd frontend && npx tsc --noEmit

build:
	cd frontend && npm run build

clean:
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

shell:
	docker compose exec backend python3 -i -c "import asyncio; from app.core.database import AsyncSessionLocal; print('GymOS shell ready')"

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev
