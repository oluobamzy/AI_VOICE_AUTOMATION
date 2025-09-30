"""
Avatar and video generation Pydantic schemas.

This module defines schemas for AI avatar creation, video synthesis,
D-ID/Synthesia integration, and face generation operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator, HttpUrl


class AvatarBase(BaseModel):
    """Base avatar schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Avatar name")
    gender: str = Field(..., description="Avatar gender")
    age_range: str = Field(..., description="Avatar age range")
    ethnicity: Optional[str] = Field(None, description="Avatar ethnicity")
    
    @validator("gender")
    def validate_gender(cls, v):
        allowed_genders = ["male", "female", "non-binary", "other"]
        if v not in allowed_genders:
            raise ValueError(f"Gender must be one of: {', '.join(allowed_genders)}")
        return v
    
    @validator("age_range")
    def validate_age_range(cls, v):
        allowed_ranges = ["child", "teen", "young_adult", "adult", "middle_aged", "senior"]
        if v not in allowed_ranges:
            raise ValueError(f"Age range must be one of: {', '.join(allowed_ranges)}")
        return v


class AvatarCreate(AvatarBase):
    """Schema for creating an avatar."""
    user_id: UUID = Field(..., description="Owner user ID")
    style: str = Field(default="realistic", description="Avatar style")
    voice_id: Optional[str] = Field(None, description="Associated voice ID")
    custom_features: Optional[Dict[str, Any]] = Field(None, description="Custom avatar features")
    reference_image_url: Optional[HttpUrl] = Field(None, description="Reference image URL")
    
    @validator("style")
    def validate_style(cls, v):
        allowed_styles = [
            "realistic", "cartoon", "anime", "artistic", "professional",
            "casual", "formal", "vintage", "modern", "abstract"
        ]
        if v not in allowed_styles:
            raise ValueError(f"Style must be one of: {', '.join(allowed_styles)}")
        return v


class AvatarCustomization(BaseModel):
    """Schema for avatar customization options."""
    hair_color: Optional[str] = Field(None, description="Hair color")
    hair_style: Optional[str] = Field(None, description="Hair style")
    eye_color: Optional[str] = Field(None, description="Eye color")
    skin_tone: Optional[str] = Field(None, description="Skin tone")
    clothing_style: Optional[str] = Field(None, description="Clothing style")
    accessories: List[str] = Field(default_factory=list, description="Accessories")
    facial_features: Optional[Dict[str, str]] = Field(None, description="Facial feature customizations")
    background: Optional[str] = Field(None, description="Background setting")
    lighting: Optional[str] = Field(None, description="Lighting preference")
    mood: Optional[str] = Field(None, description="Avatar mood/expression")


class AvatarResponse(BaseModel):
    """Schema for avatar response data."""
    id: UUID = Field(..., description="Avatar ID")
    name: str = Field(..., description="Avatar name")
    gender: str = Field(..., description="Avatar gender")
    age_range: str = Field(..., description="Avatar age range")
    ethnicity: Optional[str] = Field(None, description="Avatar ethnicity")
    style: str = Field(..., description="Avatar style")
    voice_id: Optional[str] = Field(None, description="Associated voice ID")
    preview_image_url: Optional[str] = Field(None, description="Preview image URL")
    model_file_path: Optional[str] = Field(None, description="3D model file path")
    customization: Optional[AvatarCustomization] = Field(None, description="Avatar customization")
    usage_count: int = Field(default=0, ge=0, description="Number of times used")
    is_active: bool = Field(default=True, description="Avatar availability status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class VideoGenerationRequest(BaseModel):
    """Schema for AI video generation request."""
    script_id: Optional[UUID] = Field(None, description="Script ID to use")
    avatar_id: Optional[UUID] = Field(None, description="Avatar ID to use")
    text: Optional[str] = Field(None, min_length=1, max_length=5000, description="Text for video")
    voice_settings: Optional[Dict[str, Any]] = Field(None, description="Voice generation settings")
    video_settings: VideoGenerationSettings = Field(..., description="Video generation settings")
    background: Optional[str] = Field(None, description="Background setting")
    
    @validator("text")
    def text_or_script_required(cls, v, values):
        if not v and "script_id" not in values:
            raise ValueError("Either text or script_id must be provided")
        return v


class VideoGenerationSettings(BaseModel):
    """Schema for video generation settings."""
    resolution: str = Field(default="1080p", description="Video resolution")
    frame_rate: int = Field(default=30, ge=15, le=60, description="Frames per second")
    duration_limit: Optional[float] = Field(None, gt=0, le=300, description="Max duration in seconds")
    aspect_ratio: str = Field(default="16:9", description="Video aspect ratio")
    quality: str = Field(default="high", description="Video quality")
    codec: str = Field(default="h264", description="Video codec")
    bitrate: Optional[str] = Field(None, description="Video bitrate")
    
    @validator("resolution")
    def validate_resolution(cls, v):
        allowed_resolutions = [
            "720p", "1080p", "1440p", "4k", "480p", "360p",
            "1920x1080", "1280x720", "3840x2160", "2560x1440"
        ]
        if v not in allowed_resolutions:
            raise ValueError(f"Resolution must be one of: {', '.join(allowed_resolutions)}")
        return v
    
    @validator("aspect_ratio")
    def validate_aspect_ratio(cls, v):
        allowed_ratios = ["16:9", "4:3", "1:1", "9:16", "21:9", "2:3"]
        if v not in allowed_ratios:
            raise ValueError(f"Aspect ratio must be one of: {', '.join(allowed_ratios)}")
        return v
    
    @validator("quality")
    def validate_quality(cls, v):
        allowed_qualities = ["low", "medium", "high", "ultra", "draft"]
        if v not in allowed_qualities:
            raise ValueError(f"Quality must be one of: {', '.join(allowed_qualities)}")
        return v
    
    @validator("codec")
    def validate_codec(cls, v):
        allowed_codecs = ["h264", "h265", "vp9", "av1", "prores"]
        if v not in allowed_codecs:
            raise ValueError(f"Codec must be one of: {', '.join(allowed_codecs)}")
        return v


class DIDVideoRequest(BaseModel):
    """Schema for D-ID video generation request."""
    source_url: Optional[HttpUrl] = Field(None, description="Source image URL")
    avatar_id: Optional[UUID] = Field(None, description="Avatar ID from our system")
    script: str = Field(..., min_length=1, description="Script for the video")
    voice_id: str = Field(..., description="Voice ID for speech")
    webhook_url: Optional[HttpUrl] = Field(None, description="Webhook for completion notification")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional D-ID configuration")


class SynthesiaVideoRequest(BaseModel):
    """Schema for Synthesia video generation request."""
    avatar: str = Field(..., description="Synthesia avatar ID")
    script: str = Field(..., min_length=1, description="Script for the video")
    title: Optional[str] = Field(None, max_length=200, description="Video title")
    description: Optional[str] = Field(None, max_length=1000, description="Video description")
    background: Optional[str] = Field(None, description="Background setting")
    music: Optional[str] = Field(None, description="Background music")
    voice_config: Optional[Dict[str, Any]] = Field(None, description="Voice configuration")


class VideoGenerationJob(BaseModel):
    """Schema for video generation job tracking."""
    id: UUID = Field(..., description="Job ID")
    user_id: UUID = Field(..., description="User ID")
    type: str = Field(..., description="Generation type")
    status: str = Field(..., description="Job status")
    progress: float = Field(default=0.0, ge=0, le=100, description="Progress percentage")
    provider: str = Field(..., description="AI video provider")
    provider_job_id: Optional[str] = Field(None, description="External provider job ID")
    script_id: Optional[UUID] = Field(None, description="Associated script ID")
    avatar_id: Optional[UUID] = Field(None, description="Associated avatar ID")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Generation settings")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    
    @validator("type")
    def validate_type(cls, v):
        allowed_types = ["avatar_video", "script_video", "custom_video", "bulk_video"]
        if v not in allowed_types:
            raise ValueError(f"Type must be one of: {', '.join(allowed_types)}")
        return v
    
    @validator("status")
    def validate_status(cls, v):
        allowed_statuses = [
            "pending", "queued", "processing", "rendering", "completed", 
            "failed", "cancelled", "timeout"
        ]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v
    
    @validator("provider")
    def validate_provider(cls, v):
        allowed_providers = ["d-id", "synthesia", "heygen", "custom", "internal"]
        if v not in allowed_providers:
            raise ValueError(f"Provider must be one of: {', '.join(allowed_providers)}")
        return v
    
    class Config:
        from_attributes = True


class VideoGenerationResult(BaseModel):
    """Schema for video generation results."""
    id: UUID = Field(..., description="Result ID")
    job_id: UUID = Field(..., description="Associated job ID")
    video_file_path: str = Field(..., description="Generated video file path")
    video_url: Optional[str] = Field(None, description="Public video URL")
    thumbnail_path: Optional[str] = Field(None, description="Video thumbnail path")
    thumbnail_url: Optional[str] = Field(None, description="Public thumbnail URL")
    duration: float = Field(..., ge=0, description="Video duration in seconds")
    file_size: int = Field(..., ge=0, description="Video file size in bytes")
    resolution: str = Field(..., description="Video resolution")
    frame_rate: int = Field(..., description="Frames per second")
    format: str = Field(..., description="Video format")
    quality_score: Optional[float] = Field(None, ge=0, le=10, description="Quality assessment score")
    processing_time: float = Field(..., ge=0, description="Total processing time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional video metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class FaceAnalysis(BaseModel):
    """Schema for face analysis results."""
    id: UUID = Field(..., description="Analysis ID")
    image_path: str = Field(..., description="Analyzed image path")
    faces_detected: int = Field(..., ge=0, description="Number of faces detected")
    primary_face: Optional[Dict[str, Any]] = Field(None, description="Primary face analysis")
    emotions: List[str] = Field(default_factory=list, description="Detected emotions")
    age_estimate: Optional[int] = Field(None, ge=0, le=120, description="Estimated age")
    gender_prediction: Optional[str] = Field(None, description="Gender prediction")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Analysis confidence scores")
    facial_landmarks: Optional[List[Dict[str, float]]] = Field(None, description="Facial landmark coordinates")
    quality_assessment: Dict[str, Any] = Field(default_factory=dict, description="Image quality metrics")
    created_at: datetime = Field(..., description="Analysis timestamp")
    
    class Config:
        from_attributes = True


class VoiceCloning(BaseModel):
    """Schema for voice cloning operations."""
    name: str = Field(..., min_length=1, max_length=100, description="Voice clone name")
    source_audio_path: str = Field(..., description="Source audio file path")
    target_language: str = Field(default="en", description="Target language for clone")
    quality: str = Field(default="high", description="Cloning quality")
    training_duration: Optional[int] = Field(None, ge=60, description="Training duration in seconds")
    
    @validator("quality")
    def validate_quality(cls, v):
        allowed_qualities = ["draft", "standard", "high", "premium"]
        if v not in allowed_qualities:
            raise ValueError(f"Quality must be one of: {', '.join(allowed_qualities)}")
        return v


class VoiceCloneResponse(BaseModel):
    """Schema for voice cloning results."""
    id: UUID = Field(..., description="Voice clone ID")
    name: str = Field(..., description="Voice clone name")
    voice_id: str = Field(..., description="Generated voice ID")
    source_audio_path: str = Field(..., description="Source audio file")
    quality: str = Field(..., description="Cloning quality")
    similarity_score: float = Field(..., ge=0, le=1, description="Voice similarity score")
    training_time: float = Field(..., ge=0, description="Training time in seconds")
    sample_audio_path: Optional[str] = Field(None, description="Sample audio file path")
    usage_count: int = Field(default=0, ge=0, description="Number of times used")
    is_active: bool = Field(default=True, description="Voice availability status")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class BatchVideoGeneration(BaseModel):
    """Schema for batch video generation."""
    name: str = Field(..., min_length=1, max_length=200, description="Batch job name")
    scripts: List[UUID] = Field(..., min_items=1, max_items=100, description="Script IDs to process")
    avatar_id: UUID = Field(..., description="Avatar to use for all videos")
    settings: VideoGenerationSettings = Field(..., description="Common video settings")
    priority: str = Field(default="normal", description="Processing priority")
    webhook_url: Optional[HttpUrl] = Field(None, description="Completion webhook URL")
    
    @validator("priority")
    def validate_priority(cls, v):
        allowed_priorities = ["low", "normal", "high", "urgent"]
        if v not in allowed_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(allowed_priorities)}")
        return v


class BatchVideoResponse(BaseModel):
    """Schema for batch video generation results."""
    id: UUID = Field(..., description="Batch job ID")
    name: str = Field(..., description="Batch job name")
    total_videos: int = Field(..., ge=1, description="Total videos to generate")
    completed_videos: int = Field(default=0, ge=0, description="Videos completed")
    failed_videos: int = Field(default=0, ge=0, description="Videos failed")
    status: str = Field(..., description="Batch job status")
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Overall progress")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    video_results: List[UUID] = Field(default_factory=list, description="Generated video result IDs")
    error_summary: Optional[str] = Field(None, description="Error summary if applicable")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @validator("status")
    def validate_batch_status(cls, v):
        allowed_statuses = [
            "pending", "processing", "completed", "partially_completed", 
            "failed", "cancelled"
        ]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v
    
    class Config:
        from_attributes = True