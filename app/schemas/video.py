"""
Video-related Pydantic schemas.

This module defines request/response schemas for video operations
with proper validation and serialization.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, HttpUrl, Field, validator


class VideoBase(BaseModel):
    """Base video schema with common fields."""
    filename: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list, max_items=20)


class VideoCreate(BaseModel):
    """Schema for creating a video from URL."""
    source_url: HttpUrl = Field(..., description="URL of the video to download")
    platform: str = Field(..., description="Source platform (tiktok, youtube, etc.)")
    description: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list, max_items=20)
    
    @validator("platform")
    def validate_platform(cls, v):
        allowed_platforms = ["tiktok", "youtube", "instagram", "twitter", "facebook"]
        if v.lower() not in allowed_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(allowed_platforms)}")
        return v.lower()


class VideoUpdate(BaseModel):
    """Schema for updating video metadata."""
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, max_items=20)


class VideoResponse(BaseModel):
    """Schema for video response data."""
    id: str = Field(..., description="Unique video identifier")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Current processing status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    source_url: Optional[str] = Field(None, description="Original source URL")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    resolution: Optional[str] = Field(None, description="Video resolution")
    format: Optional[str] = Field(None, description="Video format")
    description: Optional[str] = Field(None, description="Video description")
    tags: List[str] = Field(default_factory=list, description="Video tags")
    
    class Config:
        from_attributes = True


class VideoStatusResponse(BaseModel):
    """Schema for detailed video processing status."""
    id: str = Field(..., description="Video identifier")
    status: str = Field(..., description="Current status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    current_stage: str = Field(..., description="Current processing stage")
    stages_completed: List[str] = Field(default_factory=list)
    stages_remaining: List[str] = Field(default_factory=list)
    started_at: Optional[str] = Field(None, description="Processing start time")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    @validator("progress")
    def validate_progress(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Progress must be between 0 and 100")
        return v


class VideoMetadata(BaseModel):
    """Schema for video metadata extraction."""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    duration: Optional[float] = Field(None, gt=0)
    resolution: Optional[str] = None
    fps: Optional[float] = Field(None, gt=0)
    bitrate: Optional[int] = Field(None, gt=0)
    codec: Optional[str] = None
    audio_codec: Optional[str] = None
    thumbnail_url: Optional[str] = None
    upload_date: Optional[datetime] = None
    view_count: Optional[int] = Field(None, ge=0)
    like_count: Optional[int] = Field(None, ge=0)
    comment_count: Optional[int] = Field(None, ge=0)
    uploader: Optional[str] = None
    uploader_id: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class VideoProcessingConfig(BaseModel):
    """Schema for video processing configuration."""
    target_resolution: Optional[str] = Field("1080p", description="Target resolution")
    target_format: Optional[str] = Field("mp4", description="Target format")
    quality: Optional[str] = Field("high", description="Processing quality")
    enable_transcription: bool = Field(True, description="Enable transcription")
    enable_script_rewrite: bool = Field(True, description="Enable script rewriting")
    enable_avatar_generation: bool = Field(True, description="Enable avatar generation")
    avatar_template: Optional[str] = Field(None, description="Avatar template ID")
    voice_model: Optional[str] = Field(None, description="TTS voice model")
    
    @validator("target_resolution")
    def validate_resolution(cls, v):
        if v:
            allowed_resolutions = ["480p", "720p", "1080p", "1440p", "4k"]
            if v not in allowed_resolutions:
                raise ValueError(f"Resolution must be one of: {', '.join(allowed_resolutions)}")
        return v
    
    @validator("quality")
    def validate_quality(cls, v):
        if v:
            allowed_qualities = ["low", "medium", "high", "ultra"]
            if v not in allowed_qualities:
                raise ValueError(f"Quality must be one of: {', '.join(allowed_qualities)}")
        return v