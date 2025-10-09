"""
Celery tasks package.

This package contains all Celery tasks for asynchronous processing
including video processing, AI operations, publishing, and workflow orchestration.
"""

from app.tasks.celery_app import celery_app

# Import all task modules to register tasks
from app.tasks import video_tasks
from app.tasks import ai_tasks
from app.tasks import publishing_tasks  # Re-enabled with minimal imports
from app.tasks import workflow_tasks

__all__ = [
    "celery_app",
    "video_tasks",
    "ai_tasks", 
    "publishing_tasks",  # Re-enabled
    "workflow_tasks",
]