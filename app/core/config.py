"""
Application configuration management.

This module handles all configuration settings using Pydantic Settings
with environment variable support and validation.
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, RedisDsn, validator


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
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "ai_video_automation"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=str(values.get("POSTGRES_PORT")),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[RedisDsn] = None
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            password=values.get("REDIS_PASSWORD"),
            host=values.get("REDIS_HOST"),
            port=str(values.get("REDIS_PORT")),
            path=f"/{values.get('REDIS_DB') or 0}",
        )
    
    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    
    @validator("CELERY_BROKER_URL", pre=True)
    def assemble_celery_broker(cls, v: str, values: Dict[str, Any]) -> str:
        if v:
            return v
        return str(values.get("REDIS_URL")) or "redis://localhost:6379/0"
    
    @validator("CELERY_RESULT_BACKEND", pre=True)
    def assemble_celery_backend(cls, v: str, values: Dict[str, Any]) -> str:
        if v:
            return v
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
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = None
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