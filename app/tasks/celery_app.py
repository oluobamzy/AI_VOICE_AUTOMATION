"""
Celery application configuration.

This module sets up the Celery application with Redis backend,
task routing, and monitoring configuration for the AI video automation pipeline.
"""

from celery import Celery
from celery.signals import task_failure, task_success, worker_ready, worker_shutdown

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

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
    "cleanup-published-files": {
        "task": "app.tasks.publishing_tasks.cleanup_published_files_task",
        "schedule": 86400.0,  # Run daily
        "kwargs": {"retention_days": 7}
    },
    "cleanup-workflow-artifacts": {
        "task": "app.tasks.workflow_tasks.cleanup_workflow_artifacts",
        "schedule": 43200.0,  # Run twice daily
        "kwargs": {"cleanup_after_days": 3}
    }
}

# Error and event handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    logger.info(f"Request: {self.request!r}")
    return {"status": "debug_task_completed", "worker": self.request.hostname}


# Task failure handler
@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """Handle task failures globally."""
    logger.error(f"Task {task_id} failed: {exception}")
    logger.error(f"Traceback: {traceback}")
    
    # TODO: Implement failure notifications
    # Could send email, Slack notification, etc.


# Task success handler
@task_success.connect
def task_success_handler(sender=None, task_id=None, result=None, **kwargs):
    """Handle task success globally."""
    logger.info(f"Task {task_id} completed successfully")
    
    # TODO: Implement success tracking
    # Could update database, send notifications, etc.


# Worker ready handler
@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready event."""
    logger.info(f"Worker {sender.hostname} is ready")


# Worker shutdown handler
@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Handle worker shutdown event."""
    logger.info(f"Worker {sender.hostname} is shutting down")