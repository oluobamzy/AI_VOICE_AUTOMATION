"""
Task monitoring and management utilities.

This module provides utilities for monitoring Celery task execution,
managing task queues, and providing real-time status updates.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from celery import current_app
from celery.result import AsyncResult
from celery.events.state import State

from app.tasks.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class TaskMonitor:
    """Monitor and manage Celery tasks."""
    
    def __init__(self):
        self.celery_app = celery_app
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get comprehensive status of a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dict containing task status information
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)
            
            status_info = {
                "task_id": task_id,
                "status": result.status,
                "result": None,
                "traceback": None,
                "children": [],
                "date_done": None,
                "task_name": None,
                "args": None,
                "kwargs": None,
                "worker": None,
                "retries": 0,
                "eta": None
            }
            
            if result.status == TaskStatus.SUCCESS:
                status_info["result"] = result.result
                status_info["date_done"] = result.date_done
                
            elif result.status == TaskStatus.FAILURE:
                status_info["result"] = str(result.result)
                status_info["traceback"] = result.traceback
                
            # Get additional info if available
            if hasattr(result, 'info') and result.info:
                if isinstance(result.info, dict):
                    status_info.update(result.info)
            
            # Get children tasks (for group/chord tasks)
            if result.children:
                status_info["children"] = [
                    {
                        "task_id": child.id,
                        "status": child.status,
                        "result": child.result if child.successful() else str(child.result)
                    }
                    for child in result.children
                ]
            
            return status_info
            
        except Exception as exc:
            logger.error(f"Failed to get task status for {task_id}: {exc}")
            return {
                "task_id": task_id,
                "status": "ERROR",
                "error": str(exc)
            }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get status of a complete workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Dict containing workflow status
        """
        try:
            workflow_result = AsyncResult(workflow_id, app=self.celery_app)
            
            workflow_status = {
                "workflow_id": workflow_id,
                "overall_status": workflow_result.status,
                "progress": 0,
                "steps": [],
                "current_step": None,
                "estimated_completion": None,
                "error": None
            }
            
            # Calculate progress based on completed steps
            if workflow_result.children:
                total_steps = len(workflow_result.children)
                completed_steps = sum(1 for child in workflow_result.children if child.successful())
                workflow_status["progress"] = int((completed_steps / total_steps) * 100)
                
                # Get detailed step information
                for i, child in enumerate(workflow_result.children):
                    step_info = {
                        "step_number": i + 1,
                        "task_id": child.id,
                        "status": child.status,
                        "name": getattr(child, 'name', f"Step {i + 1}"),
                        "result": child.result if child.successful() else None,
                        "error": str(child.result) if child.failed() else None
                    }
                    workflow_status["steps"].append(step_info)
                
                # Determine current step
                for step in workflow_status["steps"]:
                    if step["status"] in [TaskStatus.PENDING, TaskStatus.STARTED]:
                        workflow_status["current_step"] = step["step_number"]
                        break
            
            # Estimate completion time
            if workflow_status["progress"] > 0:
                # Simple estimation based on progress
                steps_per_minute = workflow_status["progress"] / 5  # Assume 5 minutes elapsed
                remaining_progress = 100 - workflow_status["progress"]
                if steps_per_minute > 0:
                    eta_minutes = remaining_progress / steps_per_minute
                    eta = datetime.utcnow() + timedelta(minutes=eta_minutes)
                    workflow_status["estimated_completion"] = eta.isoformat()
            
            return workflow_status
            
        except Exception as exc:
            logger.error(f"Failed to get workflow status for {workflow_id}: {exc}")
            return {
                "workflow_id": workflow_id,
                "overall_status": "ERROR",
                "error": str(exc)
            }
    
    def cancel_task(self, task_id: str, terminate: bool = False) -> Dict[str, Any]:
        """
        Cancel a running task.
        
        Args:
            task_id: Task identifier
            terminate: Whether to terminate immediately
            
        Returns:
            Dict containing cancellation result
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)
            
            if terminate:
                result.revoke(terminate=True)
                action = "terminated"
            else:
                result.revoke()
                action = "revoked"
            
            return {
                "task_id": task_id,
                "action": action,
                "success": True
            }
            
        except Exception as exc:
            logger.error(f"Failed to cancel task {task_id}: {exc}")
            return {
                "task_id": task_id,
                "action": "cancel_failed",
                "success": False,
                "error": str(exc)
            }
    
    def retry_failed_task(self, task_id: str) -> Dict[str, Any]:
        """
        Retry a failed task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dict containing retry result
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)
            
            if result.status != TaskStatus.FAILURE:
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": f"Task status is {result.status}, cannot retry"
                }
            
            # Get original task info
            task_name = result.name
            task_args = result.args or []
            task_kwargs = result.kwargs or {}
            
            # Submit new task with same parameters
            new_task = self.celery_app.send_task(
                task_name,
                args=task_args,
                kwargs=task_kwargs
            )
            
            return {
                "original_task_id": task_id,
                "new_task_id": new_task.id,
                "success": True
            }
            
        except Exception as exc:
            logger.error(f"Failed to retry task {task_id}: {exc}")
            return {
                "task_id": task_id,
                "success": False,
                "error": str(exc)
            }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get status of all Celery queues.
        
        Returns:
            Dict containing queue status information
        """
        try:
            inspect = self.celery_app.control.inspect()
            
            # Get active tasks
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            reserved_tasks = inspect.reserved()
            
            queue_status = {
                "timestamp": datetime.utcnow().isoformat(),
                "workers": {},
                "queues": {
                    "video_processing": {"active": 0, "scheduled": 0, "reserved": 0},
                    "ai_processing": {"active": 0, "scheduled": 0, "reserved": 0},
                    "publishing": {"active": 0, "scheduled": 0, "reserved": 0},
                    "default": {"active": 0, "scheduled": 0, "reserved": 0}
                },
                "total_tasks": {"active": 0, "scheduled": 0, "reserved": 0}
            }
            
            # Count tasks by queue
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    queue_status["workers"][worker] = len(tasks)
                    queue_status["total_tasks"]["active"] += len(tasks)
                    
                    for task in tasks:
                        queue_name = task.get("delivery_info", {}).get("routing_key", "default")
                        if queue_name in queue_status["queues"]:
                            queue_status["queues"][queue_name]["active"] += 1
            
            if scheduled_tasks:
                for worker, tasks in scheduled_tasks.items():
                    queue_status["total_tasks"]["scheduled"] += len(tasks)
                    
                    for task in tasks:
                        queue_name = task.get("delivery_info", {}).get("routing_key", "default")
                        if queue_name in queue_status["queues"]:
                            queue_status["queues"][queue_name]["scheduled"] += 1
            
            if reserved_tasks:
                for worker, tasks in reserved_tasks.items():
                    queue_status["total_tasks"]["reserved"] += len(tasks)
                    
                    for task in tasks:
                        queue_name = task.get("delivery_info", {}).get("routing_key", "default")
                        if queue_name in queue_status["queues"]:
                            queue_status["queues"][queue_name]["reserved"] += 1
            
            return queue_status
            
        except Exception as exc:
            logger.error(f"Failed to get queue status: {exc}")
            return {
                "error": str(exc),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all workers.
        
        Returns:
            Dict containing worker statistics
        """
        try:
            inspect = self.celery_app.control.inspect()
            
            stats = inspect.stats()
            registered = inspect.registered()
            
            worker_stats = {
                "timestamp": datetime.utcnow().isoformat(),
                "workers": {}
            }
            
            if stats:
                for worker, worker_stats_data in stats.items():
                    worker_info = {
                        "status": "online",
                        "total_tasks": worker_stats_data.get("total", {}),
                        "pool": worker_stats_data.get("pool", {}),
                        "uptime": worker_stats_data.get("clock", {}).get("uptime", 0),
                        "load_avg": worker_stats_data.get("rusage", {}).get("utime", 0),
                        "registered_tasks": []
                    }
                    
                    if registered and worker in registered:
                        worker_info["registered_tasks"] = list(registered[worker])
                    
                    worker_stats["workers"][worker] = worker_info
            
            return worker_stats
            
        except Exception as exc:
            logger.error(f"Failed to get worker stats: {exc}")
            return {
                "error": str(exc),
                "timestamp": datetime.utcnow().isoformat()
            }


class TaskManager:
    """Manage and coordinate Celery tasks."""
    
    def __init__(self):
        self.celery_app = celery_app
        self.monitor = TaskMonitor()
    
    def submit_video_processing_job(
        self,
        video_url: str,
        target_platforms: List[str],
        user_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit a complete video processing job.
        
        Args:
            video_url: Source video URL
            target_platforms: List of target platforms
            user_id: User identifier
            options: Additional processing options
            
        Returns:
            Dict containing job submission result
        """
        try:
            from app.tasks.workflow_tasks import complete_video_automation_workflow
            
            workflow_config = options or {}
            workflow_config.update({
                "target_platforms": target_platforms,
                "user_id": user_id
            })
            
            job = complete_video_automation_workflow.delay(
                source_url=video_url,
                target_platforms=target_platforms,
                workflow_config=workflow_config,
                user_id=user_id
            )
            
            return {
                "success": True,
                "job_id": job.id,
                "video_url": video_url,
                "target_platforms": target_platforms,
                "user_id": user_id,
                "submitted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as exc:
            logger.error(f"Failed to submit video processing job: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "video_url": video_url,
                "user_id": user_id
            }
    
    def get_user_jobs(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get jobs for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of jobs to return
            
        Returns:
            List of job information
        """
        try:
            # TODO: Implement database query to get user jobs
            # This would query the Job model to get user's job history
            
            return []
            
        except Exception as exc:
            logger.error(f"Failed to get user jobs for {user_id}: {exc}")
            return []
    
    def cleanup_completed_jobs(self, older_than_days: int = 7) -> Dict[str, Any]:
        """
        Clean up completed jobs older than specified days.
        
        Args:
            older_than_days: Jobs older than this will be cleaned up
            
        Returns:
            Dict containing cleanup results
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            
            # TODO: Implement actual cleanup logic
            # This would clean up old job records and associated files
            
            return {
                "success": True,
                "cleaned_jobs": 0,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as exc:
            logger.error(f"Failed to cleanup completed jobs: {exc}")
            return {
                "success": False,
                "error": str(exc)
            }


# Global instances
task_monitor = TaskMonitor()
task_manager = TaskManager()