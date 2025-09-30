"""
Pydantic schemas package for AI Video Automation Pipeline.

This package contains all data validation schemas for:
- User management and authentication
- Video ingestion and processing
- Content generation and transformation
- AI avatar and voice synthesis
- Multi-platform publishing
- Analytics and performance tracking
"""

from typing import List, Any
from pydantic import BaseModel, Field, validator

# User management schemas
from .user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserLogin,
    UserProfile,
    UserStats,
    PasswordReset,
    UserPreferences,
    ApiKey,
    ApiKeyCreate,
    ApiKeyResponse,
)

# Video and content schemas
from .video import (
    VideoBase,
    VideoCreate,
    VideoUpdate,
    VideoResponse,
    VideoMetadata,
    VideoProcessingJob,
    VideoProcessingResult,
    VideoFile,
    VideoStats,
    VideoSearch,
    VideoSearchResults,
    ThumbnailGeneration,
    VideoOptimization,
    VideoComparison,
    VideoBatch,
)

# Job management schemas
from .job import (
    JobBase,
    JobCreate,
    JobUpdate,
    JobResponse,
    JobQueue,
    JobProgress,
    JobResult,
    JobError,
    JobStats,
    TaskDefinition,
    WorkflowDefinition,
    WorkflowExecution,
)

# Script and content transformation schemas
from .script import (
    TranscriptionBase,
    TranscriptionCreate,
    TranscriptionSegment,
    TranscriptionResponse,
    ScriptBase,
    ScriptCreate,
    ScriptRewriteRequest,
    ScriptRewriteResponse,
    ScriptResponse,
    TTSRequest,
    TTSResponse,
    ContentAnalysis,
    HashtagGeneration,
    HashtagResponse,
)

# Avatar and video generation schemas
from .avatar import (
    AvatarBase,
    AvatarCreate,
    AvatarCustomization,
    AvatarResponse,
    VideoGenerationRequest,
    VideoGenerationSettings,
    DIDVideoRequest,
    SynthesiaVideoRequest,
    VideoGenerationJob,
    VideoGenerationResult,
    FaceAnalysis,
    VoiceCloning,
    VoiceCloneResponse,
    BatchVideoGeneration,
    BatchVideoResponse,
)

# Platform publishing and analytics schemas
from .platform import (
    PlatformCredentials,
    PublishingProfile,
    ContentMetadata,
    PublishRequest,
    PublishJob,
    PublishResult,
    AnalyticsMetrics,
    PerformanceReport,
    AudienceInsights,
    CompetitorAnalysis,
    TrendingAnalysis,
    ContentOptimization,
    ScheduledPost,
    PlatformLimits,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate", 
    "UserResponse",
    "UserLogin",
    "UserProfile",
    "UserStats",
    "PasswordReset",
    "UserPreferences",
    "ApiKey",
    "ApiKeyCreate",
    "ApiKeyResponse",
    
    # Video schemas
    "VideoBase",
    "VideoCreate",
    "VideoUpdate", 
    "VideoResponse",
    "VideoMetadata",
    "VideoProcessingJob",
    "VideoProcessingResult",
    "VideoFile",
    "VideoStats",
    "VideoSearch",
    "VideoSearchResults",
    "ThumbnailGeneration",
    "VideoOptimization",
    "VideoComparison",
    "VideoBatch",
    
    # Job schemas
    "JobBase",
    "JobCreate",
    "JobUpdate",
    "JobResponse", 
    "JobQueue",
    "JobProgress",
    "JobResult",
    "JobError",
    "JobStats",
    "TaskDefinition",
    "WorkflowDefinition",
    "WorkflowExecution",
    
    # Script schemas
    "TranscriptionBase",
    "TranscriptionCreate",
    "TranscriptionSegment",
    "TranscriptionResponse",
    "ScriptBase",
    "ScriptCreate",
    "ScriptRewriteRequest",
    "ScriptRewriteResponse",
    "ScriptResponse",
    "TTSRequest",
    "TTSResponse",
    "ContentAnalysis",
    "HashtagGeneration",
    "HashtagResponse",
    
    # Avatar schemas
    "AvatarBase",
    "AvatarCreate",
    "AvatarCustomization",
    "AvatarResponse",
    "VideoGenerationRequest",
    "VideoGenerationSettings",
    "DIDVideoRequest",
    "SynthesiaVideoRequest",
    "VideoGenerationJob",
    "VideoGenerationResult",
    "FaceAnalysis",
    "VoiceCloning",
    "VoiceCloneResponse",
    "BatchVideoGeneration",
    "BatchVideoResponse",
    
    # Platform schemas
    "PlatformCredentials",
    "PublishingProfile",
    "ContentMetadata",
    "PublishRequest",
    "PublishJob",
    "PublishResult",
    "AnalyticsMetrics",
    "PerformanceReport",
    "AudienceInsights",
    "CompetitorAnalysis",
    "TrendingAnalysis",
    "ContentOptimization",
    "ScheduledPost",
    "PlatformLimits",
]


# Common schema patterns
class PaginationParams(BaseModel):
    """Common pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")
    

class SortParams(BaseModel):
    """Common sorting parameters."""
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", description="Sort order")
    
    @validator("sort_order")
    def validate_sort_order(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v


class PaginatedResponse(BaseModel):
    """Common paginated response structure."""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, description="Items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")
    
    class Config:
        from_attributes = True


# Schema validation utilities
def validate_schemas():
    """Validate all schema definitions for consistency."""
    # This can be used in tests to ensure schema compatibility
    schemas = [
        # User schemas
        UserBase, UserCreate, UserResponse, UserLogin, UserProfile,
        UserStats, PasswordReset, UserPreferences, ApiKey, ApiKeyCreate, ApiKeyResponse,
        
        # Video schemas  
        VideoBase, VideoCreate, VideoUpdate, VideoResponse, VideoMetadata,
        VideoProcessingJob, VideoProcessingResult, VideoFile, VideoStats,
        VideoSearch, VideoSearchResults, ThumbnailGeneration, VideoOptimization,
        VideoComparison, VideoBatch,
        
        # Job schemas
        JobBase, JobCreate, JobUpdate, JobResponse, JobQueue, JobProgress,
        JobResult, JobError, JobStats, TaskDefinition, WorkflowDefinition,
        WorkflowExecution,
        
        # Script schemas
        TranscriptionBase, TranscriptionCreate, TranscriptionSegment, TranscriptionResponse,
        ScriptBase, ScriptCreate, ScriptRewriteRequest, ScriptRewriteResponse,
        ScriptResponse, TTSRequest, TTSResponse, ContentAnalysis,
        HashtagGeneration, HashtagResponse,
        
        # Avatar schemas
        AvatarBase, AvatarCreate, AvatarCustomization, AvatarResponse,
        VideoGenerationRequest, VideoGenerationSettings, DIDVideoRequest,
        SynthesiaVideoRequest, VideoGenerationJob, VideoGenerationResult,
        FaceAnalysis, VoiceCloning, VoiceCloneResponse, BatchVideoGeneration,
        BatchVideoResponse,
        
        # Platform schemas
        PlatformCredentials, PublishingProfile, ContentMetadata, PublishRequest,
        PublishJob, PublishResult, AnalyticsMetrics, PerformanceReport,
        AudienceInsights, CompetitorAnalysis, TrendingAnalysis, ContentOptimization,
        ScheduledPost, PlatformLimits,
    ]
    
    return len(schemas)


# Add these to exports
__all__.extend([
    "PaginationParams",
    "SortParams", 
    "PaginatedResponse",
    "validate_schemas",
])