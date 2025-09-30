"""
SQLAlchemy models package for AI Video Automation Pipeline.

This package contains all database models for the application including:
- User management and authentication
- Video content and processing
- Script and content transformation  
- AI avatar and video generation
- Multi-platform publishing
- Job management and workflows
- Analytics and performance tracking
"""

# Import all models to ensure they are registered with SQLAlchemy
from .user import (
    User,
    UserPreferences,
    ApiKey,
    PasswordReset,
    UserSession,
)

from .video import (
    Video,
    VideoProcessingJob,
    VideoFile,
    VideoAnalytics,
)

from .script import (
    Script,
    Transcription,
    TTSGeneration,
    ContentAnalysis,
)

from .avatar import (
    Avatar,
    VideoGenerationJob,
    VoiceClone,
    BatchVideoGeneration,
)

from .platform import (
    PlatformCredentials,
    PublishingProfile,
    PublishJob,
    ScheduledPost,
    PlatformAnalytics,
    TrendingContent,
)

from .job import (
    Job,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowJobAssociation,
    JobQueue,
    JobSchedule,
)

# Export all models
__all__ = [
    # User models
    "User",
    "UserPreferences", 
    "ApiKey",
    "PasswordReset",
    "UserSession",
    
    # Video models
    "Video",
    "VideoProcessingJob",
    "VideoFile",
    "VideoAnalytics",
    
    # Script models
    "Script",
    "Transcription",
    "TTSGeneration",
    "ContentAnalysis",
    
    # Avatar models
    "Avatar",
    "VideoGenerationJob",
    "VoiceClone",
    "BatchVideoGeneration",
    
    # Platform models
    "PlatformCredentials",
    "PublishingProfile",
    "PublishJob",
    "ScheduledPost",
    "PlatformAnalytics",
    "TrendingContent",
    
    # Job models
    "Job",
    "WorkflowDefinition",
    "WorkflowExecution",
    "WorkflowJobAssociation",
    "JobQueue",
    "JobSchedule",
]

# from .video import Video  # Will be created in Task 4
# from .job import Job      # Will be created in Task 4  
# from .user import User    # Will be created in Task 4

__all__ = [
    # Model names will be added here as they are created
]