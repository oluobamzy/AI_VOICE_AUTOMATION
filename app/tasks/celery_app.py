"""
Celery application configuration.

This module configures Celery for async task processing
with proper error handling and monitoring.
"""

from celery import Celery

from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "ai_video_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.video_tasks",
        "app.tasks.ai_tasks",
        "app.tasks.publishing_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.tasks.video_tasks.*": {"queue": "video_processing"},
        "app.tasks.ai_tasks.*": {"queue": "ai_processing"},
        "app.tasks.publishing_tasks.*": {"queue": "publishing"},
    },
    
    # Task execution settings
    task_always_eager=False,
    task_eager_propagates=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Optional: Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-expired-files": {
        "task": "app.tasks.video_tasks.cleanup_expired_files",
        "schedule": 3600.0,  # Run every hour
    },
    "health-check": {
        "task": "app.tasks.video_tasks.health_check_task",
        "schedule": 300.0,  # Run every 5 minutes
    },
}