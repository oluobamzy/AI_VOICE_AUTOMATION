"""
Platform publishing and analytics database models.

This module defines SQLAlchemy models for multi-platform publishing,
social media integration, analytics, and performance tracking.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Boolean, DateTime, String, Text, Integer, Float, JSON, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base


class PlatformCredentials(Base):
    """Platform authentication credentials model."""
    
    __tablename__ = "platform_credentials"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Platform information
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(200), nullable=False)
    account_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    account_handle: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Authentication tokens
    access_token: Mapped[str] = mapped_column(Text, nullable=False)  # Encrypted
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Encrypted
    token_type: Mapped[str] = mapped_column(String(20), default="Bearer", nullable=False)
    
    # Token expiration
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    refresh_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Permissions and scopes
    scopes: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status and validation
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Error tracking
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="platform_credentials")
    publishing_profiles: Mapped[List["PublishingProfile"]] = relationship("PublishingProfile", back_populates="credentials", cascade="all, delete-orphan")
    publish_jobs: Mapped[List["PublishJob"]] = relationship("PublishJob", back_populates="credentials", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_platform_credentials_user_platform", "user_id", "platform"),
        Index("idx_platform_credentials_platform_account", "platform", "account_id"),
        Index("idx_platform_credentials_status", "is_active", "is_verified"),
        Index("idx_platform_credentials_expiry", "token_expires_at", "is_active"),
        UniqueConstraint("user_id", "platform", "account_id", name="uq_user_platform_account"),
        CheckConstraint("usage_count >= 0", name="check_creds_usage_count_non_negative"),
        CheckConstraint("error_count >= 0", name="check_creds_error_count_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<PlatformCredentials(user_id={self.user_id}, platform={self.platform}, account={self.account_handle})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.token_expires_at:
            return False
        return datetime.utcnow() > self.token_expires_at
    
    @property
    def needs_refresh(self) -> bool:
        """Check if token needs refresh (expires within 1 hour)."""
        if not self.token_expires_at:
            return False
        return datetime.utcnow() > (self.token_expires_at - timedelta(hours=1))


class PublishingProfile(Base):
    """Publishing profile for platform-specific settings."""
    
    __tablename__ = "publishing_profiles"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    credentials_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("platform_credentials.id", ondelete="CASCADE"), nullable=False)
    
    # Profile information
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Profile settings
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_publish: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Publishing configuration
    default_privacy: Mapped[str] = mapped_column(String(20), default="public", nullable=False)
    default_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    default_tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    default_hashtags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    
    # Content optimization
    title_template: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtag_strategy: Mapped[str] = mapped_column(String(50), default="trending", nullable=False)
    max_hashtags: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    
    # Scheduling settings
    auto_schedule: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    optimal_times: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Day/time preferences
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    
    # Audience targeting
    target_audience: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    geographic_targeting: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Quality settings
    video_quality: Mapped[str] = mapped_column(String(20), default="high", nullable=False)
    thumbnail_generation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    custom_thumbnail: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Analytics and tracking
    enable_analytics: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    track_engagement: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Custom platform settings
    platform_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Usage statistics
    videos_published: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="publishing_profiles")
    credentials: Mapped["PlatformCredentials"] = relationship("PlatformCredentials", back_populates="publishing_profiles")
    publish_jobs: Mapped[List["PublishJob"]] = relationship("PublishJob", back_populates="profile", cascade="all, delete-orphan")
    scheduled_posts: Mapped[List["ScheduledPost"]] = relationship("ScheduledPost", back_populates="profile", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_publishing_profiles_user_id", "user_id"),
        Index("idx_publishing_profiles_platform", "platform", "is_active"),
        Index("idx_publishing_profiles_default", "user_id", "platform", "is_default"),
        CheckConstraint("max_hashtags > 0", name="check_max_hashtags_positive"),
        CheckConstraint("videos_published >= 0", name="check_videos_published_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<PublishingProfile(id={self.id}, name={self.name}, platform={self.platform})>"


class PublishJob(Base):
    """Publishing job tracking."""
    
    __tablename__ = "publish_jobs"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publishing_profiles.id", ondelete="CASCADE"), nullable=False)
    credentials_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("platform_credentials.id", ondelete="CASCADE"), nullable=False)
    
    # Job information
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(50), default="publish", nullable=False)  # publish, update, delete
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    
    # Content metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    hashtags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Publishing settings
    privacy_setting: Mapped[str] = mapped_column(String(20), default="public", nullable=False)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    custom_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status and progress
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Platform response
    platform_post_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    platform_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    platform_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Scheduling
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Analytics tracking
    initial_views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    initial_engagement: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    video: Mapped["Video"] = relationship("Video", back_populates="publish_jobs")
    profile: Mapped["PublishingProfile"] = relationship("PublishingProfile", back_populates="publish_jobs")
    credentials: Mapped["PlatformCredentials"] = relationship("PlatformCredentials", back_populates="publish_jobs")
    analytics: Mapped[List["PlatformAnalytics"]] = relationship("PlatformAnalytics", back_populates="publish_job", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_publish_jobs_user_id", "user_id"),
        Index("idx_publish_jobs_video_id", "video_id"),
        Index("idx_publish_jobs_platform", "platform", "status"),
        Index("idx_publish_jobs_scheduled", "scheduled_for", "status"),
        Index("idx_publish_jobs_platform_post", "platform", "platform_post_id"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="check_publish_progress_range"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="check_publish_priority_range"),
        CheckConstraint("retry_count >= 0", name="check_publish_retry_count_non_negative"),
        CheckConstraint("max_retries >= 0", name="check_publish_max_retries_non_negative"),
        CheckConstraint("initial_views IS NULL OR initial_views >= 0", name="check_initial_views_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<PublishJob(id={self.id}, platform={self.platform}, status={self.status})>"
    
    @property
    def is_complete(self) -> bool:
        """Check if publish job is complete."""
        return self.status in ["published", "failed", "cancelled"]
    
    @property
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries and self.status == "failed"


class ScheduledPost(Base):
    """Scheduled content posting."""
    
    __tablename__ = "scheduled_posts"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publishing_profiles.id", ondelete="CASCADE"), nullable=False)
    
    # Scheduling information
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    
    # Content metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    hashtags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    
    # Publishing configuration
    privacy_setting: Mapped[str] = mapped_column(String(20), default="public", nullable=False)
    auto_optimize: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False, index=True)
    
    # Recurring schedule
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurrence_pattern: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    next_occurrence: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Execution tracking
    publish_job_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("publish_jobs.id"), nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    video: Mapped["Video"] = relationship("Video")
    profile: Mapped["PublishingProfile"] = relationship("PublishingProfile", back_populates="scheduled_posts")
    publish_job: Mapped[Optional["PublishJob"]] = relationship("PublishJob")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_scheduled_posts_user_id", "user_id"),
        Index("idx_scheduled_posts_time", "scheduled_time", "status"),
        Index("idx_scheduled_posts_recurring", "is_recurring", "next_occurrence"),
    )
    
    def __repr__(self) -> str:
        return f"<ScheduledPost(id={self.id}, scheduled_time={self.scheduled_time}, status={self.status})>"


class PlatformAnalytics(Base):
    """Platform-specific analytics and metrics."""
    
    __tablename__ = "platform_analytics"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    publish_job_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publish_jobs.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Time period
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_type: Mapped[str] = mapped_column(String(20), default="daily", nullable=False)
    
    # Engagement metrics
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dislikes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    saves: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Reach and impressions
    impressions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reach: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unique_viewers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Engagement rates
    click_through_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    completion_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Watch time metrics
    watch_time_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    average_view_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    retention_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Audience metrics
    subscriber_gained: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    subscriber_lost: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Traffic sources
    search_traffic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    direct_traffic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    social_traffic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    referral_traffic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Geographic and demographic data
    top_countries: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    age_demographics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    device_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Revenue metrics
    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_earnings: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Platform-specific metrics
    platform_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Data collection metadata
    data_source: Mapped[str] = mapped_column(String(50), default="api", nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    publish_job: Mapped["PublishJob"] = relationship("PublishJob", back_populates="analytics")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_platform_analytics_job_date", "publish_job_id", "date"),
        Index("idx_platform_analytics_platform", "platform", "date"),
        Index("idx_platform_analytics_period", "period_type", "date"),
        UniqueConstraint("publish_job_id", "date", "period_type", name="uq_analytics_period"),
        CheckConstraint("views >= 0", name="check_analytics_views_non_negative"),
        CheckConstraint("likes >= 0", name="check_analytics_likes_non_negative"),
        CheckConstraint("dislikes >= 0", name="check_analytics_dislikes_non_negative"),
        CheckConstraint("comments >= 0", name="check_analytics_comments_non_negative"),
        CheckConstraint("shares >= 0", name="check_analytics_shares_non_negative"),
        CheckConstraint("saves >= 0", name="check_analytics_saves_non_negative"),
        CheckConstraint("impressions IS NULL OR impressions >= 0", name="check_impressions_non_negative"),
        CheckConstraint("reach IS NULL OR reach >= 0", name="check_reach_non_negative"),
        CheckConstraint("click_through_rate IS NULL OR (click_through_rate >= 0 AND click_through_rate <= 1)", name="check_ctr_range"),
        CheckConstraint("engagement_rate IS NULL OR engagement_rate >= 0", name="check_engagement_rate_non_negative"),
        CheckConstraint("completion_rate IS NULL OR (completion_rate >= 0 AND completion_rate <= 1)", name="check_completion_rate_range"),
        CheckConstraint("retention_rate IS NULL OR (retention_rate >= 0 AND retention_rate <= 1)", name="check_retention_rate_range"),
        CheckConstraint("watch_time_minutes IS NULL OR watch_time_minutes >= 0", name="check_watch_time_non_negative"),
        CheckConstraint("revenue IS NULL OR revenue >= 0", name="check_revenue_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<PlatformAnalytics(platform={self.platform}, date={self.date}, views={self.views})>"
    
    @property
    def total_engagement(self) -> int:
        """Calculate total engagement interactions."""
        return self.likes + self.comments + self.shares + self.saves
    
    @property
    def engagement_percentage(self) -> float:
        """Calculate engagement percentage of views."""
        if self.views == 0:
            return 0.0
        return (self.total_engagement / self.views) * 100


class TrendingContent(Base):
    """Trending content analysis and tracking."""
    
    __tablename__ = "trending_content"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Content identification
    content_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    content_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Creator information
    creator_handle: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    creator_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    creator_followers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Content metadata
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    hashtags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Trending metrics
    view_count: Mapped[int] = mapped_column(Integer, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    share_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Trending analysis
    trending_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    velocity_score: Mapped[float] = mapped_column(Float, nullable=False)  # Growth rate
    virality_index: Mapped[float] = mapped_column(Float, nullable=False)  # Viral potential
    
    # Time tracking
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trending_since: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    peak_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Analysis metadata
    data_collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    analysis_confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_trending_content_platform", "platform", "trending_score"),
        Index("idx_trending_content_creator", "creator_handle", "platform"),
        Index("idx_trending_content_category", "category", "platform"),
        Index("idx_trending_content_metrics", "view_count", "trending_score"),
        Index("idx_trending_content_time", "published_at", "trending_since"),
        UniqueConstraint("platform", "content_id", name="uq_platform_content"),
        CheckConstraint("view_count >= 0", name="check_trending_views_non_negative"),
        CheckConstraint("like_count >= 0", name="check_trending_likes_non_negative"),
        CheckConstraint("comment_count >= 0", name="check_trending_comments_non_negative"),
        CheckConstraint("share_count >= 0", name="check_trending_shares_non_negative"),
        CheckConstraint("trending_score >= 0 AND trending_score <= 100", name="check_trending_score_range"),
        CheckConstraint("velocity_score >= 0", name="check_velocity_score_non_negative"),
        CheckConstraint("virality_index >= 0", name="check_virality_index_non_negative"),
        CheckConstraint("analysis_confidence >= 0 AND analysis_confidence <= 1", name="check_analysis_confidence_range"),
        CheckConstraint("creator_followers IS NULL OR creator_followers >= 0", name="check_creator_followers_non_negative"),
        CheckConstraint("peak_position IS NULL OR peak_position > 0", name="check_peak_position_positive"),
        CheckConstraint("current_position IS NULL OR current_position > 0", name="check_current_position_positive"),
    )
    
    def __repr__(self) -> str:
        return f"<TrendingContent(platform={self.platform}, creator={self.creator_handle}, score={self.trending_score})>"