"""
Application configuration management.

This module handles all configuration settings using Pydantic Settings
with environment variable support and validation.
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    """
    
    # Application
    PROJECT_NAME: str = "AI Video Automation Pipeline"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Security
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "testserver", "*"]
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    @property
    def secret_key(self) -> str:
        """Get the secret key for JWT tokens."""
        return self.SECRET_KEY
    
    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database configuration
    DATABASE_TYPE: str = "sqlite"  # sqlite or postgresql
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "ai_video_automation"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        
        values = info.data if hasattr(info, 'data') else {}
        db_type = values.get("DATABASE_TYPE", "sqlite")
        
        if db_type == "sqlite":
            return "sqlite+aiosqlite:///./ai_video_automation.db"
        else:
            # PostgreSQL
            return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None
    
    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        
        values = info.data if hasattr(info, 'data') else {}
        password_part = f":{values.get('REDIS_PASSWORD')}@" if values.get('REDIS_PASSWORD') else ""
        return f"redis://{password_part}{values.get('REDIS_HOST', 'localhost')}:{values.get('REDIS_PORT', 6379)}/{values.get('REDIS_DB', 0)}"
    
    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    
    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_celery_broker(cls, v: str, info) -> str:
        if v:
            return v
        values = info.data if hasattr(info, 'data') else {}
        return str(values.get("REDIS_URL")) or "redis://localhost:6379/0"
    
    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_backend(cls, v: str, info) -> str:
        if v:
            return v
        values = info.data if hasattr(info, 'data') else {}
        return str(values.get("REDIS_URL")) or "redis://localhost:6379/0"
    
    # File Storage
    STORAGE_TYPE: str = "local"  # local, s3, gcs
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    
    # Local storage paths
    UPLOAD_DIR: str = "/tmp/ai_video_automation/uploads"
    PROCESSED_DIR: str = "/tmp/ai_video_automation/processed"
    MEDIA_DIR: str = "/tmp/ai_video_automation/media"
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = "test-key-for-development"  # Default for testing
    ELEVENLABS_API_KEY: Optional[str] = None
    DID_API_KEY: Optional[str] = None
    SYNTHESIA_API_KEY: Optional[str] = None
    HEYGEN_API_KEY: Optional[str] = None
    
    # Social Media APIs
    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[str] = None
    TIKTOK_CLIENT_KEY: Optional[str] = None
    TIKTOK_CLIENT_SECRET: Optional[str] = None
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    # Monitoring
    ENABLE_METRICS: bool = True
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # Video Processing
    MAX_VIDEO_SIZE_MB: int = 100
    MAX_VIDEO_DURATION_SECONDS: int = 300
    SUPPORTED_VIDEO_FORMATS: List[str] = ["mp4", "mov", "avi", "mkv"]
    
    # FFmpeg
    FFMPEG_BINARY: str = "ffmpeg"
    FFPROBE_BINARY: str = "ffprobe"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()