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

# Core schemas - only import what actually exists
from .user import UserBase, UserCreate, UserResponse
from .video import VideoBase, VideoCreate, VideoResponse
from .job import JobBase, JobCreate, JobResponse

# Re-export commonly used schemas
__all__ = [
    "UserBase", "UserCreate", "UserResponse",
    "VideoBase", "VideoCreate", "VideoResponse", 
    "JobBase", "JobCreate", "JobResponse"
]
