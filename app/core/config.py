from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "AI Video Automation Pipeline"
    debug: bool = False
    version: str = "1.0.0"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost/ai_video_db"
    
    # Redis/Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # External APIs
    openai_api_key: Optional[str] = None
    youtube_api_key: Optional[str] = None
    tiktok_api_key: Optional[str] = None
    
    # Video Processing
    ffmpeg_path: str = "/usr/bin/ffmpeg"
    temp_video_dir: str = "/tmp/videos"
    max_video_size_mb: int = 100
    
    # Avatar/AI
    avatar_model: str = "gpt-4"
    voice_model: str = "eleven-labs"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()