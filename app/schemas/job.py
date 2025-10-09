"""
Job-related Pydantic schemas.

This module defines request/response schemas for job management
with proper validation and serialization.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class JobBase(BaseModel):
    """Base job schema with common fields."""
    job_type: str = Field(..., description="Type of job to execute")
    priority: int = Field(default=5, ge=1, le=10, description="Job priority (1-10)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Job parameters")


class JobCreate(JobBase):
    """Schema for creating a new job."""
    video_id: Optional[str] = Field(None, description="Associated video ID")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled execution time")
    
    @field_validator("job_type")
    @classmethod
    def validate_job_type(cls, v):
        allowed_types = [
            "video_download",
            "video_transcription", 
            "script_rewriting",
            "voice_generation",
            "avatar_generation",
            "video_processing",
            "publishing",
            "full_pipeline"
        ]
        if v not in allowed_types:
            raise ValueError(f"Job type must be one of: {', '.join(allowed_types)}")
        return v


class JobUpdate(BaseModel):
    """Schema for updating job metadata."""
    priority: Optional[int] = Field(None, ge=1, le=10)
    parameters: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None


class JobResponse(BaseModel):
    """Schema for job response data."""
    id: str = Field(..., description="Unique job identifier")
    job_type: str = Field(..., description="Type of job")
    status: str = Field(..., description="Current job status")
    priority: int = Field(..., description="Job priority")
    video_id: Optional[str] = Field(None, description="Associated video ID")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    started_at: Optional[str] = Field(None, description="Execution start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    scheduled_at: Optional[str] = Field(None, description="Scheduled execution time")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Job parameters")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    """Schema for detailed job status information."""
    id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    current_task: Optional[str] = Field(None, description="Current task being executed")
    tasks_completed: List[str] = Field(default_factory=list, description="Completed tasks")
    tasks_remaining: List[str] = Field(default_factory=list, description="Remaining tasks")
    started_at: Optional[str] = Field(None, description="Job start time")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    worker_id: Optional[str] = Field(None, description="Worker executing the job")
    retry_count: int = Field(default=0, ge=0, description="Number of retries")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    
    @field_validator("progress")
    @classmethod
    def validate_progress(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Progress must be between 0 and 100")
        return v


class TaskResult(BaseModel):
    """Schema for individual task results within a job."""
    task_name: str = Field(..., description="Name of the task")
    status: str = Field(..., description="Task status")
    started_at: datetime = Field(..., description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    duration: Optional[float] = Field(None, description="Task duration in seconds")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        from_attributes = True


class JobStatistics(BaseModel):
    """Schema for job execution statistics."""
    total_jobs: int = Field(..., ge=0, description="Total number of jobs")
    completed_jobs: int = Field(..., ge=0, description="Number of completed jobs")
    failed_jobs: int = Field(..., ge=0, description="Number of failed jobs")
    running_jobs: int = Field(..., ge=0, description="Number of currently running jobs")
    queued_jobs: int = Field(..., ge=0, description="Number of queued jobs")
    average_duration: Optional[float] = Field(None, description="Average job duration in seconds")
    success_rate: float = Field(..., ge=0, le=100, description="Job success rate percentage")
    
    @field_validator("success_rate")
    @classmethod
    def validate_success_rate(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Success rate must be between 0 and 100")
        return v


class JobQueue(BaseModel):
    """Schema for job queue information."""
    queue_name: str = Field(..., description="Name of the queue")
    pending_jobs: int = Field(..., ge=0, description="Number of pending jobs")
    active_jobs: int = Field(..., ge=0, description="Number of active jobs")
    failed_jobs: int = Field(..., ge=0, description="Number of failed jobs")
    processed_jobs: int = Field(..., ge=0, description="Total processed jobs")
    
    class Config:
        from_attributes = True