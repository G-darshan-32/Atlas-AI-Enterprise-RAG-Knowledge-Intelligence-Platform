from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "atlas_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.document_tasks",
        "app.workers.tasks.github_tasks",
        "app.workers.tasks.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.document_tasks.*": {"queue": "documents"},
        "app.workers.tasks.github_tasks.*": {"queue": "documents"},
        "app.workers.tasks.report_tasks.*": {"queue": "ai_tasks"},
    },
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    result_expires=86400,  # 24h
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "app.workers.tasks.document_tasks.cleanup_expired_tokens",
        "schedule": 3600.0,  # hourly
    },
}
