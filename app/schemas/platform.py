"""
Platform publishing and analytics Pydantic schemas.

This module defines schemas for multi-platform publishing, social media
integration, analytics tracking, and performance monitoring.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, HttpUrl


class PlatformCredentials(BaseModel):
    """Schema for platform authentication credentials."""
    platform: str = Field(..., description="Platform name")
    user_id: UUID = Field(..., description="Owner user ID")
    account_id: str = Field(..., description="Platform account identifier")
    access_token: str = Field(..., description="Platform access token")
    refresh_token: Optional[str] = Field(None, description="Platform refresh token")
    token_expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    scopes: List[str] = Field(default_factory=list, description="Granted permissions")
    is_active: bool = Field(default=True, description="Credential status")
    
    @field_validator("platform")

    
    @classmethod

    
    def validate_platform(cls, v):
        allowed_platforms = [
            "youtube", "tiktok", "instagram", "facebook", "twitter", "linkedin",
            "discord", "telegram", "reddit", "pinterest", "snapchat", "twitch"
        ]
        if v not in allowed_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(allowed_platforms)}")
        return v
    
    class Config:
        from_attributes = True


class PublishingProfile(BaseModel):
    """Schema for platform-specific publishing configuration."""
    id: UUID = Field(..., description="Profile ID")
    user_id: UUID = Field(..., description="Owner user ID")
    platform: str = Field(..., description="Target platform")
    name: str = Field(..., min_length=1, max_length=100, description="Profile name")
    is_default: bool = Field(default=False, description="Default profile for platform")
    auto_publish: bool = Field(default=False, description="Enable automatic publishing")
    publishing_schedule: Optional[Dict[str, Any]] = Field(None, description="Scheduled publishing settings")
    content_settings: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific content settings")
    hashtag_strategy: Optional[str] = Field(None, description="Hashtag strategy")
    audience_targeting: Optional[Dict[str, Any]] = Field(None, description="Audience targeting settings")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @field_validator("hashtag_strategy")

    
    @classmethod

    
    def validate_hashtag_strategy(cls, v):
        if v is None:
            return v
        allowed_strategies = ["trending", "niche", "branded", "mixed", "custom"]
        if v not in allowed_strategies:
            raise ValueError(f"Hashtag strategy must be one of: {', '.join(allowed_strategies)}")
        return v
    
    class Config:
        from_attributes = True


class ContentMetadata(BaseModel):
    """Schema for content metadata and optimization."""
    title: str = Field(..., min_length=1, max_length=200, description="Content title")
    description: Optional[str] = Field(None, max_length=2000, description="Content description")
    tags: List[str] = Field(default_factory=list, max_items=50, description="Content tags")
    hashtags: List[str] = Field(default_factory=list, max_items=30, description="Hashtags")
    category: Optional[str] = Field(None, description="Content category")
    language: str = Field(default="en", description="Content language")
    audience: str = Field(default="general", description="Target audience")
    content_warning: Optional[str] = Field(None, description="Content warning if applicable")
    thumbnail_path: Optional[str] = Field(None, description="Custom thumbnail path")
    
    @field_validator("audience")

    
    @classmethod

    
    def validate_audience(cls, v):
        allowed_audiences = [
            "general", "kids", "teens", "adults", "mature", "family_friendly",
            "educational", "entertainment", "business", "lifestyle"
        ]
        if v not in allowed_audiences:
            raise ValueError(f"Audience must be one of: {', '.join(allowed_audiences)}")
        return v


class PublishRequest(BaseModel):
    """Schema for content publishing request."""
    video_id: UUID = Field(..., description="Video to publish")
    platforms: List[str] = Field(..., min_items=1, description="Target platforms")
    metadata: ContentMetadata = Field(..., description="Content metadata")
    scheduling: Optional[Dict[str, Any]] = Field(None, description="Publishing schedule")
    privacy_settings: Dict[str, str] = Field(default_factory=dict, description="Privacy settings per platform")
    monetization: Optional[Dict[str, Any]] = Field(None, description="Monetization settings")
    custom_settings: Optional[Dict[str, Any]] = Field(None, description="Platform-specific custom settings")
    
    @field_validator("platforms", each_item=True)

    
    @classmethod

    
    def validate_platform_names(cls, v):
        allowed_platforms = [
            "youtube", "tiktok", "instagram", "facebook", "twitter", "linkedin",
            "discord", "telegram", "reddit", "pinterest", "snapchat", "twitch"
        ]
        if v not in allowed_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(allowed_platforms)}")
        return v


class PublishJob(BaseModel):
    """Schema for publishing job tracking."""
    id: UUID = Field(..., description="Publish job ID")
    user_id: UUID = Field(..., description="User ID")
    video_id: UUID = Field(..., description="Video ID")
    platform: str = Field(..., description="Target platform")
    status: str = Field(..., description="Publishing status")
    progress: float = Field(default=0.0, ge=0, le=100, description="Upload progress")
    platform_post_id: Optional[str] = Field(None, description="Platform-specific post ID")
    platform_url: Optional[str] = Field(None, description="Published content URL")
    metadata: ContentMetadata = Field(..., description="Content metadata")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    scheduled_for: Optional[datetime] = Field(None, description="Scheduled publish time")
    published_at: Optional[datetime] = Field(None, description="Actual publish time")
    created_at: datetime = Field(..., description="Job creation timestamp")
    
    @field_validator("status")

    
    @classmethod

    
    def validate_status(cls, v):
        allowed_statuses = [
            "pending", "uploading", "processing", "scheduled", "published",
            "failed", "cancelled", "draft", "review_required"
        ]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v
    
    class Config:
        from_attributes = True


class PublishResult(BaseModel):
    """Schema for publishing results."""
    job_id: UUID = Field(..., description="Associated job ID")
    platform: str = Field(..., description="Platform")
    success: bool = Field(..., description="Publishing success status")
    platform_post_id: Optional[str] = Field(None, description="Platform post ID")
    platform_url: Optional[str] = Field(None, description="Published content URL")
    views_count: Optional[int] = Field(None, ge=0, description="Initial view count")
    engagement_metrics: Optional[Dict[str, int]] = Field(None, description="Initial engagement metrics")
    publish_time: datetime = Field(..., description="Actual publish timestamp")
    error_details: Optional[str] = Field(None, description="Error details if failed")
    
    class Config:
        from_attributes = True


class AnalyticsMetrics(BaseModel):
    """Schema for content analytics metrics."""
    id: UUID = Field(..., description="Metrics ID")
    content_id: UUID = Field(..., description="Content/video ID")
    platform: str = Field(..., description="Platform")
    date: date = Field(..., description="Metrics date")
    views: int = Field(default=0, ge=0, description="View count")
    likes: int = Field(default=0, ge=0, description="Like count")
    dislikes: int = Field(default=0, ge=0, description="Dislike count")
    comments: int = Field(default=0, ge=0, description="Comment count")
    shares: int = Field(default=0, ge=0, description="Share count")
    saves: int = Field(default=0, ge=0, description="Save count")
    impressions: Optional[int] = Field(None, ge=0, description="Impression count")
    reach: Optional[int] = Field(None, ge=0, description="Reach count")
    click_through_rate: Optional[float] = Field(None, ge=0, le=1, description="Click-through rate")
    engagement_rate: Optional[float] = Field(None, ge=0, description="Engagement rate")
    watch_time_minutes: Optional[float] = Field(None, ge=0, description="Total watch time in minutes")
    average_view_duration: Optional[float] = Field(None, ge=0, description="Average view duration in seconds")
    subscriber_gained: Optional[int] = Field(None, description="Subscribers gained from this content")
    revenue: Optional[float] = Field(None, ge=0, description="Revenue generated")
    
    class Config:
        from_attributes = True


class PerformanceReport(BaseModel):
    """Schema for performance analytics report."""
    id: UUID = Field(..., description="Report ID")
    user_id: UUID = Field(..., description="User ID")
    period_start: date = Field(..., description="Report period start")
    period_end: date = Field(..., description="Report period end")
    platforms: List[str] = Field(..., description="Included platforms")
    total_videos: int = Field(..., ge=0, description="Total videos published")
    total_views: int = Field(..., ge=0, description="Total views across all content")
    total_engagement: int = Field(..., ge=0, description="Total engagement interactions")
    top_performing_video: Optional[UUID] = Field(None, description="Best performing video ID")
    worst_performing_video: Optional[UUID] = Field(None, description="Worst performing video ID")
    average_engagement_rate: float = Field(..., ge=0, description="Average engagement rate")
    growth_metrics: Dict[str, float] = Field(default_factory=dict, description="Growth comparison metrics")
    platform_breakdown: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Per-platform metrics")
    recommendations: List[str] = Field(default_factory=list, description="Performance improvement recommendations")
    created_at: datetime = Field(..., description="Report generation timestamp")
    
    class Config:
        from_attributes = True


class AudienceInsights(BaseModel):
    """Schema for audience analytics insights."""
    id: UUID = Field(..., description="Insights ID")
    user_id: UUID = Field(..., description="User ID")
    platform: str = Field(..., description="Platform")
    period_start: date = Field(..., description="Analysis period start")
    period_end: date = Field(..., description="Analysis period end")
    demographics: Dict[str, Any] = Field(default_factory=dict, description="Audience demographics")
    geographic_data: Dict[str, Any] = Field(default_factory=dict, description="Geographic distribution")
    device_data: Dict[str, Any] = Field(default_factory=dict, description="Device usage data")
    engagement_patterns: Dict[str, Any] = Field(default_factory=dict, description="Engagement behavior patterns")
    peak_activity_times: List[str] = Field(default_factory=list, description="Peak audience activity times")
    content_preferences: Dict[str, Any] = Field(default_factory=dict, description="Content preference insights")
    growth_trends: Dict[str, float] = Field(default_factory=dict, description="Audience growth trends")
    
    class Config:
        from_attributes = True


class CompetitorAnalysis(BaseModel):
    """Schema for competitor analysis data."""
    id: UUID = Field(..., description="Analysis ID")
    user_id: UUID = Field(..., description="User ID")
    competitor_name: str = Field(..., description="Competitor name/handle")
    platform: str = Field(..., description="Platform")
    analysis_date: date = Field(..., description="Analysis date")
    follower_count: Optional[int] = Field(None, ge=0, description="Competitor follower count")
    posting_frequency: Optional[float] = Field(None, ge=0, description="Posts per day")
    average_engagement: Optional[float] = Field(None, ge=0, description="Average engagement rate")
    content_types: Dict[str, int] = Field(default_factory=dict, description="Content type distribution")
    hashtag_strategy: List[str] = Field(default_factory=list, description="Common hashtags used")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance comparison")
    content_gaps: List[str] = Field(default_factory=list, description="Content opportunity gaps")
    
    class Config:
        from_attributes = True


class TrendingAnalysis(BaseModel):
    """Schema for trending content analysis."""
    id: UUID = Field(..., description="Trend analysis ID")
    platform: str = Field(..., description="Platform")
    analysis_date: date = Field(..., description="Analysis date")
    trending_hashtags: List[str] = Field(..., description="Trending hashtags")
    trending_topics: List[str] = Field(..., description="Trending topics")
    viral_content_patterns: Dict[str, Any] = Field(default_factory=dict, description="Viral content patterns")
    optimal_posting_times: List[str] = Field(default_factory=list, description="Optimal posting times")
    content_recommendations: List[str] = Field(default_factory=list, description="Content creation recommendations")
    engagement_predictions: Dict[str, float] = Field(default_factory=dict, description="Predicted engagement rates")
    
    class Config:
        from_attributes = True


class ContentOptimization(BaseModel):
    """Schema for content optimization suggestions."""
    content_id: UUID = Field(..., description="Content ID")
    platform: str = Field(..., description="Platform")
    current_performance: Dict[str, int] = Field(..., description="Current performance metrics")
    optimization_score: float = Field(..., ge=0, le=100, description="Current optimization score")
    title_suggestions: List[str] = Field(default_factory=list, description="Title optimization suggestions")
    description_suggestions: List[str] = Field(default_factory=list, description="Description improvements")
    hashtag_suggestions: List[str] = Field(default_factory=list, description="Hashtag recommendations")
    thumbnail_feedback: Optional[str] = Field(None, description="Thumbnail optimization feedback")
    timing_recommendations: List[str] = Field(default_factory=list, description="Posting time recommendations")
    predicted_improvement: Dict[str, float] = Field(default_factory=dict, description="Predicted performance improvement")
    
    class Config:
        from_attributes = True


class ScheduledPost(BaseModel):
    """Schema for scheduled content posts."""
    id: UUID = Field(..., description="Scheduled post ID")
    user_id: UUID = Field(..., description="User ID")
    video_id: UUID = Field(..., description="Video ID")
    platform: str = Field(..., description="Target platform")
    scheduled_time: datetime = Field(..., description="Scheduled publish time")
    metadata: ContentMetadata = Field(..., description="Content metadata")
    status: str = Field(default="scheduled", description="Schedule status")
    auto_optimize: bool = Field(default=False, description="Apply automatic optimizations")
    timezone: str = Field(default="UTC", description="User timezone")
    recurring: Optional[Dict[str, Any]] = Field(None, description="Recurring schedule settings")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    @field_validator("status")

    
    @classmethod

    
    def validate_schedule_status(cls, v):
        allowed_statuses = ["scheduled", "processing", "published", "failed", "cancelled"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v
    
    class Config:
        from_attributes = True


class PlatformLimits(BaseModel):
    """Schema for platform-specific limits and constraints."""
    platform: str = Field(..., description="Platform name")
    max_video_size_mb: Optional[int] = Field(None, description="Maximum video file size in MB")
    max_duration_seconds: Optional[int] = Field(None, description="Maximum video duration")
    supported_formats: List[str] = Field(default_factory=list, description="Supported video formats")
    max_title_length: Optional[int] = Field(None, description="Maximum title length")
    max_description_length: Optional[int] = Field(None, description="Maximum description length")
    max_hashtags: Optional[int] = Field(None, description="Maximum number of hashtags")
    api_rate_limits: Dict[str, int] = Field(default_factory=dict, description="API rate limits")
    content_policies: List[str] = Field(default_factory=list, description="Content policy restrictions")
    
    class Config:
        from_attributes = True