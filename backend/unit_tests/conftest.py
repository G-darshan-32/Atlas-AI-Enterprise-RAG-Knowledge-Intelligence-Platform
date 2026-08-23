"""
Standalone unit test conftest — sets env vars before any app imports.
No database, no HTTP, no external services needed.
"""
import os

# Must be set before any app module is imported
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_SYNC_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/1"
os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/2"
os.environ["SECRET_KEY"] = "test-secret-key-exactly-32-chars!!"
os.environ["OPENAI_API_KEY"] = "sk-test-not-real"
os.environ["S3_ENDPOINT_URL"] = "http://localhost:9000"
os.environ["S3_ACCESS_KEY"] = "test"
os.environ["S3_SECRET_KEY"] = "test"
os.environ["S3_BUCKET_NAME"] = "test"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["APP_ENV"] = "testing"
