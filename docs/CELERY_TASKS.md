# Celery Task Queue System

This document describes the comprehensive Celery task queue system implemented for the AI Video Automation pipeline.

## Overview

The task queue system provides asynchronous processing capabilities for:
- Video downloading and processing
- AI-powered transcription and content generation
- Multi-platform publishing
- Workflow orchestration
- Monitoring and management

## Architecture

### Queue Structure

- **video_processing**: Resource-intensive video operations
- **ai_processing**: AI service API calls and processing
- **publishing**: Platform publishing operations
- **default**: General-purpose tasks

### Task Modules

1. **video_tasks.py**: Video download, processing, and file operations
2. **ai_tasks.py**: AI services integration (OpenAI, ElevenLabs, D-ID)
3. **publishing_tasks.py**: Multi-platform publishing (YouTube, TikTok, Instagram, Twitter)
4. **workflow_tasks.py**: Complex workflow orchestration
5. **task_monitor.py**: Monitoring and management utilities

## Key Features

### Advanced Task Management
- Automatic retry with exponential backoff
- Error handling and recovery
- Progress tracking and monitoring
- Resource-aware task routing

### Workflow Orchestration
- Complex multi-step workflows using Celery primitives (group, chain, chord)
- Parallel processing for independent operations
- Sequential processing for dependent operations
- Error recovery and rollback capabilities

### Production-Ready Configuration
- Redis backend for reliability
- Task routing by queue type
- Worker specialization
- Monitoring and health checks
- Automatic cleanup of expired resources

## Usage Examples

### Basic Task Submission

```python
from app.tasks.video_tasks import download_video_task

# Submit video download task
result = download_video_task.delay(
    url="https://www.tiktok.com/@user/video/123",
    options={"format": "best[height<=1080]"}
)

# Check task status
print(f"Task ID: {result.id}")
print(f"Status: {result.status}")
```

### Workflow Orchestration

```python
from app.tasks.workflow_tasks import complete_video_automation_workflow

# Complete automation workflow
workflow_job = complete_video_automation_workflow.delay(
    source_url="https://www.tiktok.com/@user/video/123",
    target_platforms=["youtube", "instagram"],
    workflow_config={
        "style_preferences": {"tone": "engaging"},
        "generate_voice": True,
        "voice_settings": {"voice_id": "premium_voice"}
    },
    user_id="user123"
)

print(f"Workflow ID: {workflow_job.id}")
```

### Task Monitoring

```python
from app.tasks.task_monitor import task_monitor

# Get task status
status = task_monitor.get_task_status("task-id-123")
print(f"Status: {status['status']}")
print(f"Progress: {status.get('progress', 'N/A')}")

# Get queue status
queue_status = task_monitor.get_queue_status()
print(f"Active tasks: {queue_status['total_tasks']['active']}")
```

## Worker Management

### Starting Workers

```bash
# Video processing worker (2 concurrent processes)
python -m app.tasks.worker video-worker

# AI processing worker (4 concurrent processes)
python -m app.tasks.worker ai-worker

# Publishing worker (3 concurrent processes)
python -m app.tasks.worker publishing-worker

# General purpose worker
python -m app.tasks.worker general-worker

# Celery Beat scheduler for periodic tasks
python -m app.tasks.worker beat

# Flower monitoring dashboard
python -m app.tasks.worker flower
```

### Supervisor Configuration

Use the provided `supervisord.conf` for production deployment with automatic restart and logging.

## Monitoring

### Flower Dashboard
- Access at http://localhost:5555
- Real-time task monitoring
- Worker statistics
- Queue management

### Task Status API
```python
# Get comprehensive task status
status = task_monitor.get_task_status(task_id)

# Get workflow status with progress
workflow_status = task_monitor.get_workflow_status(workflow_id)

# Get queue statistics
queue_stats = task_monitor.get_queue_status()

# Get worker statistics
worker_stats = task_monitor.get_worker_stats()
```

## Error Handling

### Automatic Retry
- Exponential backoff for transient failures
- Maximum retry limits per task type
- Different retry strategies for different error types

### Failure Recovery
- Global error handlers
- Task failure notifications
- Dead letter queue for permanent failures

### Monitoring and Alerting
- Health check tasks
- Worker status monitoring
- Queue depth monitoring
- Performance metrics

## Performance Optimization

### Task Routing
- Resource-intensive tasks routed to specialized workers
- API-bound tasks use higher concurrency
- CPU-bound tasks use lower concurrency

### Resource Management
- Memory-aware task distribution
- Automatic cleanup of temporary files
- Connection pooling for external services

### Scaling
- Horizontal scaling with additional workers
- Queue-specific scaling based on load
- Auto-scaling integration support

## Testing

Run the comprehensive test suite:

```bash
python test_celery.py
```

Tests include:
- Connection verification
- Basic task execution
- Health checks
- Monitoring functionality
- Queue status
- Worker statistics

## Configuration

### Environment Variables

```bash
# Redis configuration
REDIS_URL=redis://localhost:6379/0

# Celery configuration
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Worker configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
```

### Production Settings

```python
# app/core/config.py
CELERY_CONFIG = {
    "broker_url": REDIS_URL,
    "result_backend": REDIS_URL,
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "result_expires": 3600,
    "timezone": "UTC",
    "enable_utc": True,
}
```

## Periodic Tasks

### Scheduled Cleanup
- Expired file cleanup (hourly)
- Published file cleanup (daily)
- Workflow artifact cleanup (twice daily)
- Health checks (every 5 minutes)

### Custom Schedules
```python
# Add to celery_app.py beat_schedule
"custom-task": {
    "task": "app.tasks.custom.custom_task",
    "schedule": crontab(minute=0, hour=0),  # Daily at midnight
}
```

## Security

### Task Authentication
- User context in task execution
- Permission checks for sensitive operations
- Audit logging for all operations

### Data Protection
- Secure handling of API keys
- Encryption of sensitive task data
- Secure inter-service communication

## Troubleshooting

### Common Issues

1. **Worker Connection Errors**
   - Check Redis connectivity
   - Verify worker configuration
   - Check firewall settings

2. **Task Timeouts**
   - Increase task timeout settings
   - Check resource availability
   - Monitor worker load

3. **Memory Issues**
   - Reduce worker concurrency
   - Implement task result cleanup
   - Monitor memory usage

### Debugging Tools

```bash
# Check worker status
celery -A app.tasks.celery_app inspect active

# Check queue lengths
celery -A app.tasks.celery_app inspect reserved

# Purge specific queue
celery -A app.tasks.celery_app purge -Q queue_name
```

## Best Practices

### Task Design
- Keep tasks idempotent
- Use appropriate timeouts
- Handle errors gracefully
- Log operations comprehensively

### Workflow Design
- Break complex operations into smaller tasks
- Use appropriate Celery primitives
- Implement proper error recovery
- Monitor workflow progress

### Production Deployment
- Use supervisor for worker management
- Implement proper logging
- Monitor queue depths
- Set up alerting for failures