"""
Custom exceptions for the AI Video Automation application.

This module defines custom exception classes for different components
and operations within the application.
"""

from typing import Optional, Any, Dict


class AppException(Exception):
    """Base exception class for application-specific errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppException):
    """Raised when data validation fails."""
    pass


class AuthenticationError(AppException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(AppException):
    """Raised when authorization fails."""
    pass


class DatabaseError(AppException):
    """Raised when database operations fail."""
    pass


class ExternalServiceError(AppException):
    """Raised when external service calls fail."""
    pass


# Video processing exceptions
class VideoProcessingError(AppException):
    """Raised when video processing operations fail."""
    pass


class VideoDownloadError(VideoProcessingError):
    """Raised when video download fails."""
    pass


class VideoFormatError(VideoProcessingError):
    """Raised when video format is invalid or unsupported."""
    pass


# AI service exceptions
class AIServiceError(AppException):
    """Base exception for AI service errors."""
    pass


class TranscriptionError(AIServiceError):
    """Raised when transcription operations fail."""
    pass


class ContentGenerationError(AIServiceError):
    """Raised when AI content generation fails."""
    pass


class VoiceSynthesisError(AIServiceError):
    """Raised when voice synthesis fails."""
    pass


class AvatarGenerationError(AIServiceError):
    """Raised when avatar generation fails."""
    pass


# Audio processing exceptions
class AudioProcessingError(AppException):
    """Raised when audio processing operations fail."""
    pass


class AudioExtractionError(AudioProcessingError):
    """Raised when audio extraction from video fails."""
    pass


class AudioFormatError(AudioProcessingError):
    """Raised when audio format is invalid or unsupported."""
    pass


# Publishing exceptions
class PublishingError(AppException):
    """Raised when content publishing fails."""
    pass


class PlatformError(PublishingError):
    """Raised when platform-specific operations fail."""
    pass


class UploadError(PublishingError):
    """Raised when content upload fails."""
    pass


# File system exceptions
class FileSystemError(AppException):
    """Raised when file system operations fail."""
    pass


class FileNotFoundError(FileSystemError):
    """Raised when a required file is not found."""
    pass


class StorageError(FileSystemError):
    """Raised when storage operations fail."""
    pass


# Task queue exceptions
class TaskError(AppException):
    """Raised when task queue operations fail."""
    pass


class TaskTimeoutError(TaskError):
    """Raised when a task times out."""
    pass


class TaskRetryError(TaskError):
    """Raised when a task fails after maximum retries."""
    pass


# Configuration exceptions
class ConfigurationError(AppException):
    """Raised when configuration is invalid or missing."""
    pass


class EnvironmentError(ConfigurationError):
    """Raised when environment variables are missing or invalid."""
    pass


# Rate limiting exceptions
class RateLimitError(AppException):
    """Raised when rate limits are exceeded."""
    pass


class QuotaExceededError(AppException):
    """Raised when usage quotas are exceeded."""
    pass