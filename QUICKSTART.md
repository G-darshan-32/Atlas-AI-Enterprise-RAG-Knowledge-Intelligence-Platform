    # Atlas AI — Developer Quickstart

## Prerequisites

- Docker Desktop (or Docker Engine + Compose)
- Node.js 20+
- Python 3.11+
- An OpenAI API key

---

## 1. Clone and configure

```bash
git clone https://github.com/your-org/atlas-ai.git
cd atlas-ai
cp .env.example .env
```

Edit `.env` — the only required change for local dev:

```
OPENAI_API_KEY=sk-your-key-here
```

---

## 2. Start infrastructure services

```bash
docker compose up -d postgres redis qdrant minio
```

Wait ~10 seconds for PostgreSQL to be ready.

---

## 3. Run database migrations

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
```

---

## 4. Seed demo data

```bash
python scripts/seed.py
```

This creates 4 demo workspaces and 5 demo users.

---

## 5. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

## 6. Start Celery worker (document processing)

```bash
celery -A app.workers.celery_app worker -Q documents -c 2 --loglevel=info
```

---

## 7. Start the frontend

```bash
cd ../frontend
npm install
npm run dev
```

Frontend: http://localhost:3000

---

## Demo Login Credentials

| Role        | Email                         | Password       |
|-------------|-------------------------------|----------------|
| Super Admin | admin@atlas-ai.com            | Admin@123456   |
| Engineer    | dev@technova.com              | Demo@123456    |
| HR Manager  | hr@technova.com               | Demo@123456    |
| Researcher  | researcher@atlas-ai.com       | Demo@123456    |

---

## Running All Services with Docker Compose

For a fully containerized setup:

```bash
docker compose up
```

Wait ~60 seconds for all services to initialize, then:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed.py
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

---

## Service URLs

| Service          | URL                           |
|------------------|-------------------------------|
| Frontend         | http://localhost:3000         |
| Backend API      | http://localhost:8000         |
| API Docs         | http://localhost:8000/docs    |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| MinIO Console    | http://localhost:9001         |
| Redis            | localhost:6379                |
| PostgreSQL       | localhost:5432                |

---

## Architecture Overview

```
Client (Next.js) → Nginx → FastAPI → PostgreSQL
                                   → Redis (cache/queue)
                                   → Qdrant (vectors)
                                   → MinIO (files)
                        → Celery Workers → Document pipeline
                        → LangGraph Agents → OpenAI
```

## Key Features to Try

1. **Upload a document** → Documents page → drag & drop a PDF
2. **Chat with it** → Chat page → ask questions about the document
3. **Semantic search** → Search page → natural language query
4. **Connect a GitHub repo** → Repositories → connect `owner/repo`
5. **Generate a report** → Reports → click "Workspace Summary"
6. **View analytics** → Analytics page → charts and metrics
