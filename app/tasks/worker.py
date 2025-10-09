"""
Celery worker startup and management script.

This script provides utilities for starting and managing Celery workers
with proper configuration for the AI video automation pipeline.
"""

import os
import sys
import argparse
from typing import List, Optional

from celery import Celery
from celery.bin import worker

from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def start_worker(
    queues: Optional[List[str]] = None,
    concurrency: Optional[int] = None,
    loglevel: str = "info",
    worker_name: Optional[str] = None
):
    """
    Start a Celery worker with specified configuration.
    
    Args:
        queues: List of queues to consume from
        concurrency: Number of concurrent worker processes
        loglevel: Logging level
        worker_name: Custom worker name
    """
    try:
        logger.info("Starting Celery worker...")
        
        # Default queues based on worker type
        if queues is None:
            queues = ["default", "video_processing", "ai_processing", "publishing"]
        
        # Default concurrency based on CPU count
        if concurrency is None:
            concurrency = os.cpu_count() or 4
        
        # Default worker name
        if worker_name is None:
            worker_name = f"worker-{os.getpid()}"
        
        # Worker arguments
        worker_args = [
            "--app=app.tasks.celery_app:celery_app",
            f"--queues={','.join(queues)}",
            f"--concurrency={concurrency}",
            f"--loglevel={loglevel}",
            f"--hostname={worker_name}@%h",
            "--events",
            "--heartbeat-interval=30",
            "--without-gossip",
            "--without-mingle"
        ]
        
        logger.info(f"Worker configuration:")
        logger.info(f"  Queues: {queues}")
        logger.info(f"  Concurrency: {concurrency}")
        logger.info(f"  Log level: {loglevel}")
        logger.info(f"  Worker name: {worker_name}")
        
        # Start the worker
        worker_instance = worker.worker(app=celery_app)
        worker_instance.run_from_argv("celery", worker_args)
        
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as exc:
        logger.error(f"Worker failed to start: {exc}")
        sys.exit(1)


def start_video_worker():
    """Start a worker specialized for video processing tasks."""
    start_worker(
        queues=["video_processing"],
        concurrency=2,  # Lower concurrency for resource-intensive video tasks
        worker_name="video-worker"
    )


def start_ai_worker():
    """Start a worker specialized for AI processing tasks."""
    start_worker(
        queues=["ai_processing"],
        concurrency=4,  # Higher concurrency for AI API calls
        worker_name="ai-worker"
    )


def start_publishing_worker():
    """Start a worker specialized for publishing tasks."""
    start_worker(
        queues=["publishing"],
        concurrency=3,  # Moderate concurrency for API calls
        worker_name="publishing-worker"
    )


def start_general_worker():
    """Start a general-purpose worker for all queues."""
    start_worker(
        queues=["default", "video_processing", "ai_processing", "publishing"],
        concurrency=4,
        worker_name="general-worker"
    )


def start_beat_scheduler():
    """Start Celery Beat scheduler for periodic tasks."""
    try:
        logger.info("Starting Celery Beat scheduler...")
        
        from celery.bin import beat
        
        beat_args = [
            "--app=app.tasks.celery_app:celery_app",
            "--loglevel=info",
            "--schedule=/tmp/celerybeat-schedule"
        ]
        
        beat_instance = beat.beat(app=celery_app)
        beat_instance.run_from_argv("celery", beat_args)
        
    except KeyboardInterrupt:
        logger.info("Beat scheduler stopped by user")
    except Exception as exc:
        logger.error(f"Beat scheduler failed to start: {exc}")
        sys.exit(1)


def start_flower_monitor():
    """Start Flower monitoring dashboard."""
    try:
        logger.info("Starting Flower monitoring dashboard...")
        
        from flower.command import FlowerCommand
        
        flower_args = [
            "--app=app.tasks.celery_app:celery_app",
            "--port=5555",
            "--address=0.0.0.0",
            "--basic_auth=admin:secret",  # Change in production
            "--persistent=True",
            "--db=/tmp/flower.db"
        ]
        
        flower_cmd = FlowerCommand()
        flower_cmd.run_from_argv("flower", flower_args)
        
    except KeyboardInterrupt:
        logger.info("Flower monitor stopped by user")
    except Exception as exc:
        logger.error(f"Flower monitor failed to start: {exc}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Celery worker management")
    parser.add_argument(
        "command",
        choices=[
            "worker",
            "video-worker", 
            "ai-worker",
            "publishing-worker",
            "general-worker",
            "beat",
            "flower"
        ],
        help="Command to run"
    )
    parser.add_argument(
        "--queues",
        nargs="+",
        help="Queues to consume from"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        help="Number of concurrent processes"
    )
    parser.add_argument(
        "--loglevel",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging level"
    )
    parser.add_argument(
        "--name",
        help="Custom worker name"
    )
    
    args = parser.parse_args()
    
    # Set up environment
    if not settings.REDIS_URL:
        logger.error("Redis URL not configured")
        sys.exit(1)
    
    # Execute command
    if args.command == "worker":
        start_worker(
            queues=args.queues,
            concurrency=args.concurrency,
            loglevel=args.loglevel,
            worker_name=args.name
        )
    elif args.command == "video-worker":
        start_video_worker()
    elif args.command == "ai-worker":
        start_ai_worker()
    elif args.command == "publishing-worker":
        start_publishing_worker()
    elif args.command == "general-worker":
        start_general_worker()
    elif args.command == "beat":
        start_beat_scheduler()
    elif args.command == "flower":
        start_flower_monitor()


if __name__ == "__main__":
    main()