"""
Video database models.

This module defines SQLAlchemy models for video content management,
processing jobs, metadata, and file handling.
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Boolean, DateTime, String, Text, Integer, Float, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, LargeBinary
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base


class Video(Base):
    """Video model for content management."""
    
    __tablename__ = "videos"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Basic video information
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    source_video_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    
    # Video metadata
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Duration in seconds
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Size in bytes
    format: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    frame_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    aspect_ratio: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Bitrate in kbps
    
    # File paths and storage
    original_file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    processed_file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    audio_file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Content categorization
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False, index=True)
    
    # Processing status
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False, index=True)
    processing_progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Quality and analysis
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-10 quality rating
    content_rating: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    has_audio: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_subtitles: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Visibility and permissions
    visibility: Mapped[str] = mapped_column(String(20), default="private", nullable=False, index=True)
    is_original: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parent_video_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=True)
    
    # Analytics and engagement
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="videos")
    parent_video: Mapped[Optional["Video"]] = relationship("Video", remote_side=[id], back_populates="derived_videos")
    derived_videos: Mapped[List["Video"]] = relationship("Video", back_populates="parent_video", cascade="all, delete-orphan")
    processing_jobs: Mapped[List["VideoProcessingJob"]] = relationship("VideoProcessingJob", back_populates="video", cascade="all, delete-orphan")
    scripts: Mapped[List["Script"]] = relationship("Script", back_populates="video", cascade="all, delete-orphan")
    transcriptions: Mapped[List["Transcription"]] = relationship("Transcription", back_populates="video", cascade="all, delete-orphan")
    generation_jobs: Mapped[List["VideoGenerationJob"]] = relationship("VideoGenerationJob", back_populates="source_video", foreign_keys="VideoGenerationJob.source_video_id", cascade="all, delete-orphan")
    publish_jobs: Mapped[List["PublishJob"]] = relationship("PublishJob", back_populates="video", cascade="all, delete-orphan")
    analytics: Mapped[List["VideoAnalytics"]] = relationship("VideoAnalytics", back_populates="video", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_videos_user_id", "user_id"),
        Index("idx_videos_status", "status", "processing_progress"),
        Index("idx_videos_source", "source_platform", "source_video_id"),
        Index("idx_videos_created", "created_at", "user_id"),
        Index("idx_videos_visibility", "visibility", "deleted_at"),
        Index("idx_videos_category_tags", "category", "language"),
        Index("idx_videos_quality", "quality_score", "status"),
        CheckConstraint("processing_progress >= 0 AND processing_progress <= 100", name="check_progress_range"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 10)", name="check_quality_range"),
        CheckConstraint("duration IS NULL OR duration > 0", name="check_duration_positive"),
        CheckConstraint("file_size IS NULL OR file_size > 0", name="check_file_size_positive"),
        CheckConstraint("view_count >= 0", name="check_view_count_non_negative"),
        CheckConstraint("download_count >= 0", name="check_download_count_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<Video(id={self.id}, title={self.title[:30]}, status={self.status})>"
    
    @property
    def is_processed(self) -> bool:
        """Check if video processing is complete."""
        return self.status == "completed" and self.processing_progress == 100.0
    
    @property
    def is_deleted(self) -> bool:
        """Check if video is soft deleted."""
        return self.deleted_at is not None
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if not self.duration:
            return "00:00"
        
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def file_size_formatted(self) -> str:
        """Get formatted file size string."""
        if not self.file_size:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"


class VideoProcessingJob(Base):
    """Video processing job tracking."""
    
    __tablename__ = "video_processing_jobs"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    video_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    
    # Job information
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)  # 1-10, higher is more urgent
    
    # Processing details
    processor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Which service/worker handled this
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Input/Output configuration
    input_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    result_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Error handling
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Timing
    estimated_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Estimated seconds
    actual_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Actual seconds
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="processing_jobs")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_processing_jobs_video_id", "video_id"),
        Index("idx_processing_jobs_type_status", "job_type", "status"),
        Index("idx_processing_jobs_priority", "priority", "created_at"),
        Index("idx_processing_jobs_status_progress", "status", "progress"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="check_job_progress_range"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="check_priority_range"),
        CheckConstraint("retry_count >= 0", name="check_retry_count_non_negative"),
        CheckConstraint("max_retries >= 0", name="check_max_retries_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<VideoProcessingJob(id={self.id}, type={self.job_type}, status={self.status})>"
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status in ["completed", "failed", "cancelled"]
    
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


class VideoFile(Base):
    """Video file variants and formats."""
    
    __tablename__ = "video_files"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    video_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    
    # File information
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # original, processed, thumbnail, etc.
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # File properties
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    codec: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    frame_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Storage and access
    storage_provider: Mapped[str] = mapped_column(String(50), default="local", nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    public_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Processing metadata
    processing_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    quality_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    video: Mapped["Video"] = relationship("Video")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_video_files_video_id", "video_id"),
        Index("idx_video_files_type", "file_type", "video_id"),
        Index("idx_video_files_availability", "is_available", "storage_provider"),
        UniqueConstraint("video_id", "file_type", "format", name="uq_video_file_variant"),
        CheckConstraint("file_size > 0", name="check_video_file_size_positive"),
        CheckConstraint("duration IS NULL OR duration > 0", name="check_video_file_duration_positive"),
    )
    
    def __repr__(self) -> str:
        return f"<VideoFile(id={self.id}, type={self.file_type}, format={self.format})>"


class VideoAnalytics(Base):
    """Video analytics and metrics."""
    
    __tablename__ = "video_analytics"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    video_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    
    # Time period for metrics
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    period_type: Mapped[str] = mapped_column(String(20), default="daily", nullable=False)  # daily, weekly, monthly
    
    # View metrics
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    watch_time_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_view_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    completion_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Percentage who watched to end
    
    # Engagement metrics
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dislikes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bookmarks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Traffic sources
    direct_traffic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    search_traffic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    social_traffic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    referral_traffic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Geographic and demographic data
    top_countries: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    device_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    age_demographics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Platform-specific metrics
    platform_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="analytics")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_video_analytics_video_date", "video_id", "date"),
        Index("idx_video_analytics_period", "period_type", "date"),
        UniqueConstraint("video_id", "date", "period_type", name="uq_video_analytics_period"),
        CheckConstraint("views >= 0", name="check_views_non_negative"),
        CheckConstraint("unique_views >= 0", name="check_unique_views_non_negative"),
        CheckConstraint("watch_time_seconds >= 0", name="check_watch_time_non_negative"),
        CheckConstraint("completion_rate IS NULL OR (completion_rate >= 0 AND completion_rate <= 100)", name="check_completion_rate_range"),
        CheckConstraint("unique_views <= views", name="check_unique_views_logical"),
    )
    
    def __repr__(self) -> str:
        return f"<VideoAnalytics(video_id={self.video_id}, date={self.date}, views={self.views})>"
    
    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate."""
        if self.views == 0:
            return 0.0
        total_engagement = self.likes + self.comments + self.shares
        return (total_engagement / self.views) * 100