.PHONY: up down migrate seed test lint dev-backend dev-frontend

# Start all infrastructure (postgres, redis, qdrant, minio)
infra:
	docker compose up -d postgres redis qdrant minio

# Start everything
up:
	docker compose up -d

# Stop everything
down:
	docker compose down

# Run migrations
migrate:
	cd backend && alembic upgrade head

# Seed demo data
seed:
	cd backend && python scripts/seed.py

# Run backend tests
test:
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

# Lint backend
lint-backend:
	cd backend && ruff check app/

# Lint frontend
lint-frontend:
	cd frontend && npm run lint

# Start backend dev server
dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

# Start Celery worker
worker:
	cd backend && celery -A app.workers.celery_app worker -Q documents,ai_tasks -c 2 --loglevel=info

# Start frontend dev server
dev-frontend:
	cd frontend && npm run dev

# Full local setup (first time)
setup: infra
	@echo "Waiting for services..."
	@sleep 8
	cd backend && pip install -r requirements.txt && alembic upgrade head && python scripts/seed.py
	cd frontend && npm install
	@echo "Setup complete. Run 'make dev-backend' and 'make dev-frontend' in separate terminals."

# Rebuild and restart
rebuild:
	docker compose build --no-cache
	docker compose up -d
