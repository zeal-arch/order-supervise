.PHONY: help up down dev-api dev-worker dev-web test seed clean

help:
	@echo "Available commands:"
	@echo "  make up          - Start PostgreSQL and Temporal in Docker"
	@echo "  make down        - Stop all Docker containers"
	@echo "  make dev-api     - Run FastAPI backend locally"
	@echo "  make dev-worker  - Run Temporal Python worker locally"
	@echo "  make dev-web     - Run Next.js frontend locally"
	@echo "  make test        - Run test suite (unit + workflow)"
	@echo "  make seed        - Seed default supervisor configs and sample orders"

up:
	docker-compose up -d

down:
	docker-compose down

dev-api:
	.\.venv\Scripts\uvicorn apps.api.app.main:app --reload --port 8000

dev-worker:
	.\.venv\Scripts\python -m temporal.worker

dev-web:
	cd apps/web && npm run dev

test:
	.\.venv\Scripts\pytest -v tests/

seed:
	.\.venv\Scripts\python database/seed.py
