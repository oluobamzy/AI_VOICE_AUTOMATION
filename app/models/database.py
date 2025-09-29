from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from app.models.schemas import VideoStatus, PlatformType

Base = declarative_base()


class VideoModel(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    source_url = Column(String(500), nullable=False)
    processed_url = Column(String(500))
    thumbnail_url = Column(String(500))
    platform = Column(SQLEnum(PlatformType), nullable=False)
    status = Column(SQLEnum(VideoStatus), default=VideoStatus.PENDING)
    duration = Column(Float)
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ProcessingTaskModel(Base):
    __tablename__ = "processing_tasks"

    id = Column(String(255), primary_key=True)
    video_id = Column(Integer, nullable=False)
    status = Column(SQLEnum(VideoStatus), default=VideoStatus.PENDING)
    progress = Column(Float, default=0.0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())