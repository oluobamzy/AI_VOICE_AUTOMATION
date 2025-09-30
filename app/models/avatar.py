"""
Avatar and video generation database models.

This module defines SQLAlchemy models for AI avatar management,
video generation jobs, and related operations.
"""

from datetime import datetime
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


class Avatar(Base):
    """Avatar model for AI video generation."""
    
    __tablename__ = "avatars"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Basic information
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_type: Mapped[str] = mapped_column(String(50), default="realistic", nullable=False, index=True)
    
    # Physical characteristics
    gender: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    age_range: Mapped[str] = mapped_column(String(20), nullable=False)
    ethnicity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hair_color: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    eye_color: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    skin_tone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    
    # Style and appearance
    style: Mapped[str] = mapped_column(String(50), default="realistic", nullable=False)
    clothing_style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    background_preference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mood_expression: Mapped[str] = mapped_column(String(30), default="neutral", nullable=False)
    
    # Technical specifications
    resolution: Mapped[str] = mapped_column(String(20), default="1080p", nullable=False)
    format: Mapped[str] = mapped_column(String(20), default="mp4", nullable=False)
    quality_preset: Mapped[str] = mapped_column(String(20), default="high", nullable=False)
    
    # Associated voice and assets
    voice_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    voice_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    preview_image_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    preview_video_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    model_file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Customization options
    customization_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    facial_features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    animation_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    lighting_preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Provider integration
    provider: Mapped[str] = mapped_column(String(50), default="internal", nullable=False, index=True)
    provider_avatar_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    provider_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status and availability
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Usage and analytics
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # User ratings 1-5
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Creation and training metadata
    creation_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Time to create in seconds
    training_samples: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-10
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="avatars")
    generation_jobs: Mapped[List["VideoGenerationJob"]] = relationship("VideoGenerationJob", back_populates="avatar", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_avatars_user_id", "user_id"),
        Index("idx_avatars_type_style", "avatar_type", "style"),
        Index("idx_avatars_provider", "provider", "provider_avatar_id"),
        Index("idx_avatars_status", "status", "is_public"),
        Index("idx_avatars_usage", "usage_count", "rating"),
        Index("idx_avatars_characteristics", "gender", "age_range", "ethnicity"),
        CheckConstraint("usage_count >= 0", name="check_avatar_usage_count_non_negative"),
        CheckConstraint("generation_count >= 0", name="check_avatar_generation_count_non_negative"),
        CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 5)", name="check_avatar_rating_range"),
        CheckConstraint("rating_count >= 0", name="check_avatar_rating_count_non_negative"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 10)", name="check_avatar_quality_range"),
        CheckConstraint("similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1)", name="check_avatar_similarity_range"),
        CheckConstraint("creation_time IS NULL OR creation_time > 0", name="check_creation_time_positive"),
        CheckConstraint("training_samples IS NULL OR training_samples > 0", name="check_training_samples_positive"),
    )
    
    def __repr__(self) -> str:
        return f"<Avatar(id={self.id}, name={self.name}, type={self.avatar_type})>"
    
    @property
    def is_deleted(self) -> bool:
        """Check if avatar is soft deleted."""
        return self.deleted_at is not None
    
    @property
    def average_rating(self) -> float:
        """Get average rating."""
        return self.rating or 0.0
    
    def increment_usage(self):
        """Increment usage counter."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()


class VideoGenerationJob(Base):
    """Video generation job tracking."""
    
    __tablename__ = "video_generation_jobs"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    avatar_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("avatars.id", ondelete="CASCADE"), nullable=False)
    script_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("scripts.id", ondelete="SET NULL"), nullable=True)
    source_video_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    
    # Job configuration
    job_type: Mapped[str] = mapped_column(String(50), default="avatar_video", nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)  # 1-10
    
    # Content input
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    input_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    
    # Generation settings
    generation_settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    video_settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    voice_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Provider configuration
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider_job_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    provider_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status and progress
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    current_step: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Output information
    output_video_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    output_video_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    preview_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Video metadata
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    format: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Processing analytics
    processing_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Total time in seconds
    queue_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Time in queue
    generation_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Actual generation time
    cost_estimate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    credits_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Error handling
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Scheduling and timing
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Webhook and notifications
    webhook_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    avatar: Mapped["Avatar"] = relationship("Avatar", back_populates="generation_jobs")
    script: Mapped[Optional["Script"]] = relationship("Script")
    source_video: Mapped[Optional["Video"]] = relationship("Video", back_populates="generation_jobs", foreign_keys=[source_video_id])
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_generation_jobs_user_id", "user_id"),
        Index("idx_generation_jobs_avatar_id", "avatar_id"),
        Index("idx_generation_jobs_status", "status", "priority"),
        Index("idx_generation_jobs_provider", "provider", "provider_job_id"),
        Index("idx_generation_jobs_timing", "created_at", "started_at", "completed_at"),
        Index("idx_generation_jobs_scheduled", "scheduled_at", "status"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="check_generation_progress_range"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="check_generation_priority_range"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 10)", name="check_generation_quality_range"),
        CheckConstraint("duration IS NULL OR duration > 0", name="check_generation_duration_positive"),
        CheckConstraint("file_size IS NULL OR file_size > 0", name="check_generation_file_size_positive"),
        CheckConstraint("processing_time IS NULL OR processing_time > 0", name="check_generation_processing_time_positive"),
        CheckConstraint("cost_estimate IS NULL OR cost_estimate >= 0", name="check_cost_estimate_non_negative"),
        CheckConstraint("credits_used IS NULL OR credits_used >= 0", name="check_credits_used_non_negative"),
        CheckConstraint("retry_count >= 0", name="check_generation_retry_count_non_negative"),
        CheckConstraint("max_retries >= 0", name="check_generation_max_retries_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<VideoGenerationJob(id={self.id}, status={self.status}, progress={self.progress})>"
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status in ["completed", "failed", "cancelled"]
    
    @property
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries and self.status == "failed"
    
    @property
    def total_processing_time(self) -> Optional[float]:
        """Get total processing time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class VoiceClone(Base):
    """Voice cloning model for custom voice generation."""
    
    __tablename__ = "voice_clones"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Voice information
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Source material
    source_audio_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_duration: Mapped[float] = mapped_column(Float, nullable=False)  # Seconds
    source_quality: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Voice characteristics
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    age_estimate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    accent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    
    # Cloning configuration
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider_voice_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    cloning_model: Mapped[str] = mapped_column(String(100), nullable=False)
    quality_setting: Mapped[str] = mapped_column(String(20), default="high", nullable=False)
    
    # Training and quality metrics
    training_time: Mapped[float] = mapped_column(Float, nullable=False)  # Seconds
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-10
    naturalness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-10
    
    # Sample and preview
    sample_audio_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    sample_text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    preview_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Status and availability
    status: Mapped[str] = mapped_column(String(50), default="training", nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Cost and billing
    training_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    credits_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    trained_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_voice_clones_user_id", "user_id"),
        Index("idx_voice_clones_provider", "provider", "provider_voice_id"),
        Index("idx_voice_clones_status", "status", "is_active"),
        Index("idx_voice_clones_quality", "similarity_score", "quality_score"),
        UniqueConstraint("provider", "provider_voice_id", name="uq_provider_voice"),
        CheckConstraint("source_duration > 0", name="check_source_duration_positive"),
        CheckConstraint("age_estimate IS NULL OR (age_estimate >= 0 AND age_estimate <= 120)", name="check_age_estimate_range"),
        CheckConstraint("training_time > 0", name="check_training_time_positive"),
        CheckConstraint("similarity_score >= 0 AND similarity_score <= 1", name="check_voice_similarity_range"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 10)", name="check_voice_quality_range"),
        CheckConstraint("naturalness_score IS NULL OR (naturalness_score >= 0 AND naturalness_score <= 10)", name="check_voice_naturalness_range"),
        CheckConstraint("usage_count >= 0", name="check_voice_usage_count_non_negative"),
        CheckConstraint("generation_count >= 0", name="check_voice_generation_count_non_negative"),
        CheckConstraint("training_cost IS NULL OR training_cost >= 0", name="check_training_cost_non_negative"),
        CheckConstraint("credits_used IS NULL OR credits_used >= 0", name="check_voice_credits_used_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<VoiceClone(id={self.id}, name={self.name}, status={self.status})>"
    
    @property
    def is_ready(self) -> bool:
        """Check if voice clone is ready for use."""
        return self.status == "completed" and self.is_active
    
    @property
    def is_deleted(self) -> bool:
        """Check if voice clone is soft deleted."""
        return self.deleted_at is not None


class BatchVideoGeneration(Base):
    """Batch video generation for processing multiple videos."""
    
    __tablename__ = "batch_video_generations"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    avatar_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("avatars.id", ondelete="CASCADE"), nullable=False)
    
    # Batch information
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuration
    generation_settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    video_settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    voice_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Input data
    script_ids: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)  # UUIDs as strings
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status and progress
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    total_jobs: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_jobs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_jobs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Timing
    estimated_completion: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Results and output
    result_video_ids: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    failed_job_ids: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    output_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Error handling
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Notifications
    webhook_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    avatar: Mapped["Avatar"] = relationship("Avatar")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_batch_generations_user_id", "user_id"),
        Index("idx_batch_generations_avatar_id", "avatar_id"),
        Index("idx_batch_generations_status", "status", "priority"),
        Index("idx_batch_generations_progress", "progress_percentage", "status"),
        CheckConstraint("total_jobs > 0", name="check_total_jobs_positive"),
        CheckConstraint("completed_jobs >= 0", name="check_completed_jobs_non_negative"),
        CheckConstraint("failed_jobs >= 0", name="check_failed_jobs_non_negative"),
        CheckConstraint("completed_jobs <= total_jobs", name="check_completed_jobs_logical"),
        CheckConstraint("failed_jobs <= total_jobs", name="check_failed_jobs_logical"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", name="check_batch_progress_range"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="check_batch_priority_range"),
    )
    
    def __repr__(self) -> str:
        return f"<BatchVideoGeneration(id={self.id}, name={self.name}, status={self.status})>"
    
    @property
    def is_complete(self) -> bool:
        """Check if batch generation is complete."""
        return self.status in ["completed", "partially_completed", "failed", "cancelled"]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_jobs == 0:
            return 0.0
        return (self.completed_jobs / self.total_jobs) * 100