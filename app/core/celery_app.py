from celery import Celery
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "ai_video_automation",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.ingest.tasks",
        "app.transform.tasks", 
        "app.avatar.tasks",
        "app.publish.tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "app.ingest.tasks.*": {"queue": "ingest"},
        "app.transform.tasks.*": {"queue": "transform"},
        "app.avatar.tasks.*": {"queue": "avatar"},
        "app.publish.tasks.*": {"queue": "publish"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)