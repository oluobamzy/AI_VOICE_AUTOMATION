from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class VideoStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PlatformType(str, Enum):
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"


class VideoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    tags: List[str] = Field(default_factory=list)
    duration: Optional[float] = Field(None, gt=0)


class VideoCreate(VideoBase):
    source_url: HttpUrl
    platform: PlatformType


class VideoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = None
    status: Optional[VideoStatus] = None


class Video(VideoBase):
    id: int
    status: VideoStatus
    platform: PlatformType
    source_url: str
    processed_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProcessingTask(BaseModel):
    id: str
    video_id: int
    status: VideoStatus
    progress: float = Field(0.0, ge=0.0, le=100.0)
    error_message: Optional[str] = None
    created_at: datetime


class AvatarConfig(BaseModel):
    voice_id: str = Field(..., min_length=1)
    voice_speed: float = Field(1.0, ge=0.5, le=2.0)
    voice_pitch: float = Field(1.0, ge=0.5, le=2.0)
    background_music: bool = False
    avatar_style: str = "realistic"


class PublishConfig(BaseModel):
    platform: PlatformType
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    tags: List[str] = Field(default_factory=list)
    scheduled_time: Optional[datetime] = None
    privacy_setting: str = "public"


class VideoProcessingRequest(BaseModel):
    video_id: int
    avatar_config: Optional[AvatarConfig] = None
    publish_config: Optional[PublishConfig] = None
    custom_script: Optional[str] = None
    
    
class HealthCheck(BaseModel):
    status: str = "healthy"
    version: str
    timestamp: datetime
    services: Dict[str, str] = Field(default_factory=dict)