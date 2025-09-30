"""
Job and workflow database models.

This module defines SQLAlchemy models for job management,
task queuing, workflow execution, and background processing.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Boolean, DateTime, String, Text, Integer, Float, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base


class Job(Base):
    """General job model for background task management."""
    
    __tablename__ = "jobs"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Job classification
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Task and function information
    task_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)  # Celery task name
    function_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    module_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Priority and scheduling
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False, index=True)  # 1-10
    queue: Mapped[str] = mapped_column(String(100), default="default", nullable=False, index=True)
    
    # Job parameters
    args: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Positional arguments
    kwargs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Keyword arguments
    
    # Status and progress
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    current_step: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    total_steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Execution tracking
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, unique=True, index=True)
    worker_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    worker_hostname: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Result and output
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_files: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    
    # Error handling
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Timing and performance
    estimated_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Estimated seconds
    timeout: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Timeout in seconds
    
    # Dependencies
    depends_on: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)  # Job IDs
    blocks: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)  # Job IDs this blocks
    
    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    delay_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Execution timestamps
    queued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Lifecycle timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")
    workflow_executions: Mapped[List["WorkflowExecution"]] = relationship("WorkflowExecution", secondary="workflow_job_associations", back_populates="jobs")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_jobs_type_status", "job_type", "status"),
        Index("idx_jobs_category_priority", "category", "priority"),
        Index("idx_jobs_queue_status", "queue", "status"),
        Index("idx_jobs_scheduled", "scheduled_at", "status"),
        Index("idx_jobs_worker", "worker_id", "status"),
        Index("idx_jobs_timing", "created_at", "started_at", "completed_at"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="check_job_priority_range"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="check_job_progress_range"),
        CheckConstraint("retry_count >= 0", name="check_job_retry_count_non_negative"),
        CheckConstraint("max_retries >= 0", name="check_job_max_retries_non_negative"),
        CheckConstraint("timeout IS NULL OR timeout > 0", name="check_job_timeout_positive"),
        CheckConstraint("estimated_duration IS NULL OR estimated_duration > 0", name="check_job_estimated_duration_positive"),
        CheckConstraint("total_steps IS NULL OR total_steps > 0", name="check_job_total_steps_positive"),
    )
    
    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status in ["completed", "failed", "cancelled", "revoked"]
    
    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status in ["started", "running", "processing"]
    
    @property
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries and self.status == "failed"
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Get job duration in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    @property
    def wait_time_seconds(self) -> Optional[int]:
        """Get time job waited in queue before starting."""
        if self.queued_at and self.started_at:
            return int((self.started_at - self.queued_at).total_seconds())
        return None


class WorkflowDefinition(Base):
    """Workflow definition for complex multi-step processes."""
    
    __tablename__ = "workflow_definitions"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Workflow information
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Workflow configuration
    definition: Mapped[dict] = mapped_column(JSON, nullable=False)  # Workflow structure
    default_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Default parameters
    
    # Steps and tasks
    steps: Mapped[dict] = mapped_column(JSON, nullable=False)  # Step definitions
    dependencies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Step dependencies
    
    # Status and availability
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    average_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Average in seconds
    
    # Validation and constraints
    input_schema: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_schema: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    executions: Mapped[List["WorkflowExecution"]] = relationship("WorkflowExecution", back_populates="workflow_definition", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_workflow_definitions_name_version", "name", "version"),
        Index("idx_workflow_definitions_category", "category", "is_active"),
        Index("idx_workflow_definitions_usage", "usage_count", "success_rate"),
        UniqueConstraint("name", "version", name="uq_workflow_name_version"),
        CheckConstraint("usage_count >= 0", name="check_workflow_usage_count_non_negative"),
        CheckConstraint("success_rate >= 0 AND success_rate <= 100", name="check_workflow_success_rate_range"),
        CheckConstraint("average_duration IS NULL OR average_duration > 0", name="check_workflow_avg_duration_positive"),
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowDefinition(name={self.name}, version={self.version})>"


class WorkflowExecution(Base):
    """Workflow execution instance."""
    
    __tablename__ = "workflow_executions"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_definition_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Execution information
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    execution_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    
    # Configuration
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status and progress
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    current_step: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    completed_steps: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    failed_steps: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    total_steps: Mapped[int] = mapped_column(Integer, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Results and output
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    step_results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Results by step
    
    # Error handling
    error_step: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Priority and scheduling
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    workflow_definition: Mapped["WorkflowDefinition"] = relationship("WorkflowDefinition", back_populates="executions")
    user: Mapped[Optional["User"]] = relationship("User")
    jobs: Mapped[List["Job"]] = relationship("Job", secondary="workflow_job_associations", back_populates="workflow_executions")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_workflow_executions_definition_id", "workflow_definition_id"),
        Index("idx_workflow_executions_user_id", "user_id"),
        Index("idx_workflow_executions_status", "status", "priority"),
        Index("idx_workflow_executions_timing", "created_at", "started_at", "completed_at"),
        CheckConstraint("total_steps > 0", name="check_workflow_total_steps_positive"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="check_workflow_progress_range"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="check_workflow_priority_range"),
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, status={self.status}, progress={self.progress})>"
    
    @property
    def is_complete(self) -> bool:
        """Check if workflow execution is complete."""
        return self.status in ["completed", "failed", "cancelled"]
    
    @property
    def success_rate(self) -> float:
        """Calculate step success rate."""
        if self.total_steps == 0:
            return 0.0
        return (len(self.completed_steps) / self.total_steps) * 100
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Get workflow execution duration in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None


# Association table for many-to-many relationship between workflows and jobs
class WorkflowJobAssociation(Base):
    """Association table for workflow executions and jobs."""
    
    __tablename__ = "workflow_job_associations"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_execution_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    # Association metadata
    step_name: Mapped[str] = mapped_column(String(200), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Failure stops workflow
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_workflow_job_assoc_workflow", "workflow_execution_id"),
        Index("idx_workflow_job_assoc_job", "job_id"),
        Index("idx_workflow_job_assoc_step", "workflow_execution_id", "step_name", "step_order"),
        UniqueConstraint("workflow_execution_id", "job_id", name="uq_workflow_job"),
        CheckConstraint("step_order >= 0", name="check_step_order_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowJobAssociation(workflow={self.workflow_execution_id}, job={self.job_id}, step={self.step_name})>"


class JobQueue(Base):
    """Job queue configuration and management."""
    
    __tablename__ = "job_queues"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Queue information
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Queue configuration
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_workers: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_jobs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Max jobs in queue
    
    # Queue behavior
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_scale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Rate limiting
    rate_limit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "10/m" for 10 per minute
    
    # Queue statistics
    jobs_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_processing_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Seconds
    
    # Queue settings
    default_timeout: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Default job timeout
    retry_policy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_job_queues_priority", "priority", "is_active"),
        Index("idx_job_queues_stats", "jobs_processed", "jobs_failed"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="check_queue_priority_range"),
        CheckConstraint("max_workers > 0", name="check_max_workers_positive"),
        CheckConstraint("max_jobs IS NULL OR max_jobs > 0", name="check_max_jobs_positive"),
        CheckConstraint("jobs_processed >= 0", name="check_jobs_processed_non_negative"),
        CheckConstraint("jobs_failed >= 0", name="check_jobs_failed_non_negative"),
        CheckConstraint("average_processing_time IS NULL OR average_processing_time > 0", name="check_avg_processing_time_positive"),
        CheckConstraint("default_timeout IS NULL OR default_timeout > 0", name="check_default_timeout_positive"),
    )
    
    def __repr__(self) -> str:
        return f"<JobQueue(name={self.name}, priority={self.priority}, active={self.is_active})>"
    
    @property
    def success_rate(self) -> float:
        """Calculate queue success rate."""
        total = self.jobs_processed + self.jobs_failed
        if total == 0:
            return 100.0
        return (self.jobs_processed / total) * 100


class JobSchedule(Base):
    """Scheduled job configuration."""
    
    __tablename__ = "job_schedules"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Schedule information
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Job configuration
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    args: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    kwargs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    queue: Mapped[str] = mapped_column(String(100), default="default", nullable=False)
    
    # Schedule configuration
    schedule_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # cron, interval, once
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    interval_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status and control
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_runs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Maximum executions
    runs_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timing
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    max_failures: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_job_schedules_next_run", "next_run_at", "is_active"),
        Index("idx_job_schedules_type", "schedule_type", "is_active"),
        Index("idx_job_schedules_task", "task_name", "is_active"),
        CheckConstraint("max_runs IS NULL OR max_runs > 0", name="check_max_runs_positive"),
        CheckConstraint("runs_completed >= 0", name="check_runs_completed_non_negative"),
        CheckConstraint("interval_seconds IS NULL OR interval_seconds > 0", name="check_interval_seconds_positive"),
        CheckConstraint("max_failures >= 0", name="check_max_failures_non_negative"),
        CheckConstraint("failure_count >= 0", name="check_failure_count_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<JobSchedule(name={self.name}, type={self.schedule_type}, active={self.is_active})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if schedule has reached max runs."""
        return self.max_runs is not None and self.runs_completed >= self.max_runs
    
    @property
    def should_run(self) -> bool:
        """Check if schedule should run now."""
        if not self.is_active or self.is_expired:
            return False
        if self.failure_count >= self.max_failures:
            return False
        if not self.next_run_at:
            return False
        return datetime.utcnow() >= self.next_run_at