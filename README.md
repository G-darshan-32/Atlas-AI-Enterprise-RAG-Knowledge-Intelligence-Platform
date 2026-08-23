# Atlas AI

Atlas AI is a full-stack enterprise knowledge workspace. Teams can organize documents into isolated workspaces, search their knowledge base, ask questions through an AI chat interface, connect GitHub repositories, and view usage analytics.

The project combines a Next.js frontend with a FastAPI backend, PostgreSQL persistence, JWT authentication, background processing, vector search, and S3-compatible file storage.

## Features

- Multi-tenant workspaces with member roles and workspace-level access control
- Email/password authentication with bcrypt password hashing and JWT access tokens
- Refresh-token rotation, logout, email verification, and password reset flows
- Document upload, folders, processing status, chunking, and indexed knowledge
- AI chat and retrieval-augmented generation over workspace documents
- Semantic search powered by Qdrant
- GitHub repository connection and repository indexing workflows
- Reports, analytics, notifications, audit logs, and API key management
- Responsive dark interface built for repeated knowledge-work tasks

## Screenshots

### Welcome page

![Atlas AI welcome page](docs/screenshots/welcome.png)

### Registration

![Atlas AI registration screen](docs/screenshots/register.png)

### Workspace selection

![Atlas AI workspace selection](docs/screenshots/workspaces.png)

### Knowledge dashboard

![Atlas AI knowledge dashboard](docs/screenshots/dashboard.png)

### AI chat

![Atlas AI chat interface](docs/screenshots/chat.png)

## Technology

| Area | Technology |
| --- | --- |
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS, Zustand, React Query |
| Backend | FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| Authentication | JWT access tokens, rotating refresh tokens, bcrypt |
| AI | LangGraph, LangChain, Groq, retrieval-augmented generation |
| Database | PostgreSQL |
| Vector search | Qdrant |
| Cache and queue | Redis, Celery |
| Object storage | S3-compatible storage, MinIO for local development |
| Deployment | Docker Compose, Nginx, GitHub Actions |

## Project Structure

```text
atlas-ai/
├── backend/                  FastAPI application and database migrations
│   ├── app/api/              REST API routes
│   ├── app/ai/               AI orchestration and retrieval pipeline
│   ├── app/models/           SQLAlchemy models
│   ├── app/services/         Authentication, email, and storage services
│   ├── scripts/seed.py       Demo data and users
│   └── tests/                Integration tests
├── frontend/                 Next.js application
│   └── src/                  Pages, components, hooks, and client stores
├── docs/                     Product documentation and screenshots
├── infrastructure/           Nginx and monitoring configuration
├── docker-compose.yml        Local multi-service development environment
└── .github/workflows/        CI and deployment workflows
```

## Requirements

For the complete application, install:

- Node.js 20 or newer
- Python 3.11 or newer
- PostgreSQL 16
- Redis
- Qdrant
- MinIO or another S3-compatible storage service
- A Groq API key for AI features

Docker Desktop is the easiest way to run the supporting services. Manual setup is also supported; see the [manual setup](#manual-setup) section.

## API Key Required

You must use your own Groq API key to enable AI features. The value in `.env.example` is only a placeholder and will not work. Create an account with Groq, generate your key, and set it in your local environment file:

```env
GROQ_API_KEY=your-own-groq-api-key
```

Never share or commit your API key. Keep it in `.env` or `backend/.env`, both of which are ignored by Git. Each developer or deployment must configure its own key.

## Docker Setup

From the repository root:

```bash
cp .env.example .env
```

Edit `.env`, replace the placeholder with your own `GROQ_API_KEY`, and then start the services:

```bash
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed.py
```

Open the application at <http://localhost:3000>.

## Manual Setup

Start PostgreSQL first and create a database and user:

```sql
CREATE USER atlas WITH PASSWORD 'atlas_dev_password';
CREATE DATABASE atlas_ai OWNER atlas;
```

In `backend/.env`, use local service addresses such as:

```env
DATABASE_URL=postgresql+asyncpg://atlas:atlas_dev_password@localhost:5432/atlas_ai
DATABASE_SYNC_URL=postgresql://atlas:atlas_dev_password@localhost:5432/atlas_ai
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
S3_ENDPOINT_URL=http://localhost:9000
```

Run the backend in one terminal:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py
python -m uvicorn app.main:app --reload --port 8000
```

On Windows Git Bash, activate the virtual environment with:

```bash
source venv/Scripts/activate
```

Run the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>. For basic login, PostgreSQL is required; Redis, Qdrant, and MinIO are needed for their related features.

## Demo Accounts

The seed script creates these local development accounts:

| Role | Email | Password |
| --- | --- | --- |
| Super Admin | `admin@atlas-ai.com` | `Admin@123456` |
| Engineer | `dev@technova.com` | `Demo@123456` |
| HR Manager | `hr@technova.com` | `Demo@123456` |
| Researcher | `researcher@atlas-ai.com` | `Demo@123456` |

Do not use these credentials in production.

## Service URLs

| Service | URL |
| --- | --- |
| Frontend | <http://localhost:3000> |
| Backend API | <http://localhost:8000> |
| API docs | <http://localhost:8000/docs> |
| Qdrant dashboard | <http://localhost:6333/dashboard> |
| MinIO console | <http://localhost:9001> |

## Testing

```bash
cd backend
pytest tests/ -v
```

The integration tests expect PostgreSQL-compatible types. The default SQLite test fixture cannot represent PostgreSQL `ARRAY` columns.

## Security and Configuration

- Never commit `.env`, `.env.local`, production environment files, API keys, passwords, private keys, or certificates.
- Copy `.env.example` to create a local environment file.
- Use a strong random `SECRET_KEY` outside local development.
- Configure OAuth callback URLs and `ALLOWED_ORIGINS` for the deployed domain.
- Review the deployment secrets referenced by `.github/workflows/deploy.yml` before enabling production deployment.

## License

No license has been declared yet. Add a license before distributing this project publicly.
