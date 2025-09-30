"""
Script and content database models.

This module defines SQLAlchemy models for script management,
transcription, content transformation, and TTS operations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Boolean, DateTime, String, Text, Integer, Float, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base


class Script(Base):
    """Script model for content generation and management."""
    
    __tablename__ = "scripts"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    
    # Content information
    title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    original_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Before any modifications
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False, index=True)
    
    # Content metadata
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_reading_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # Minutes
    estimated_speech_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # Minutes
    
    # Categorization and tagging
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    
    # Style and audience settings
    style: Mapped[str] = mapped_column(String(50), default="engaging", nullable=False)
    target_audience: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    tone: Mapped[str] = mapped_column(String(50), default="friendly", nullable=False)
    formality_level: Mapped[str] = mapped_column(String(20), default="casual", nullable=False)
    
    # Source and transformation
    source_type: Mapped[str] = mapped_column(String(50), default="original", nullable=False, index=True)  # original, transcription, rewrite, template
    source_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)  # Reference to source (transcription, parent script, etc.)
    transformation_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # rewrite, summarize, expand, translate
    
    # Quality and analysis
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-10 rating
    readability_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100 Flesch reading ease
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # -1 to 1
    engagement_prediction: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    
    # Version control
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_script_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("scripts.id"), nullable=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    template_variables: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status and workflow
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # AI processing metadata
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    processing_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Seconds
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Times used for video generation
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="scripts")
    video: Mapped[Optional["Video"]] = relationship("Video", back_populates="scripts")
    parent_script: Mapped[Optional["Script"]] = relationship("Script", remote_side=[id], back_populates="child_scripts")
    child_scripts: Mapped[List["Script"]] = relationship("Script", back_populates="parent_script", cascade="all, delete-orphan")
    transcription: Mapped[Optional["Transcription"]] = relationship("Transcription", back_populates="script", uselist=False)
    tts_generations: Mapped[List["TTSGeneration"]] = relationship("TTSGeneration", back_populates="script", cascade="all, delete-orphan")
    content_analysis: Mapped[Optional["ContentAnalysis"]] = relationship("ContentAnalysis", back_populates="script", uselist=False, cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_scripts_user_id", "user_id"),
        Index("idx_scripts_video_id", "video_id"),
        Index("idx_scripts_source", "source_type", "source_id"),
        Index("idx_scripts_status", "status", "is_archived"),
        Index("idx_scripts_category", "category", "language"),
        Index("idx_scripts_quality", "quality_score", "engagement_prediction"),
        Index("idx_scripts_created", "created_at", "user_id"),
        Index("idx_scripts_template", "is_template", "is_public"),
        CheckConstraint("word_count >= 0", name="check_word_count_non_negative"),
        CheckConstraint("character_count >= 0", name="check_character_count_non_negative"),
        CheckConstraint("estimated_reading_time >= 0", name="check_reading_time_non_negative"),
        CheckConstraint("estimated_speech_time >= 0", name="check_speech_time_non_negative"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 10)", name="check_quality_score_range"),
        CheckConstraint("readability_score IS NULL OR (readability_score >= 0 AND readability_score <= 100)", name="check_readability_range"),
        CheckConstraint("sentiment_score IS NULL OR (sentiment_score >= -1 AND sentiment_score <= 1)", name="check_sentiment_range"),
        CheckConstraint("engagement_prediction IS NULL OR (engagement_prediction >= 0 AND engagement_prediction <= 100)", name="check_engagement_range"),
        CheckConstraint("ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)", name="check_ai_confidence_range"),
        CheckConstraint("version >= 1", name="check_version_positive"),
        CheckConstraint("usage_count >= 0", name="check_usage_count_non_negative"),
        CheckConstraint("generation_count >= 0", name="check_generation_count_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<Script(id={self.id}, title={self.title or 'Untitled'}, word_count={self.word_count})>"
    
    @property
    def is_deleted(self) -> bool:
        """Check if script is soft deleted."""
        return self.deleted_at is not None
    
    def calculate_metrics(self):
        """Calculate content metrics."""
        words = len(self.content.split())
        characters = len(self.content)
        
        # Estimate reading time (average 200 words per minute)
        reading_time = words / 200.0
        
        # Estimate speech time (average 150 words per minute)
        speech_time = words / 150.0
        
        self.word_count = words
        self.character_count = characters
        self.estimated_reading_time = reading_time
        self.estimated_speech_time = speech_time


class Transcription(Base):
    """Transcription model for audio/video to text conversion."""
    
    __tablename__ = "transcriptions"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    video_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    script_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("scripts.id", ondelete="SET NULL"), nullable=True)
    
    # Audio source information
    audio_file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_language: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    detected_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    language_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Transcription content
    text: Mapped[str] = mapped_column(Text, nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Unprocessed transcription
    segments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Time-segmented transcription
    
    # Processing details
    model_used: Mapped[str] = mapped_column(String(100), default="whisper-1", nullable=False)
    processing_time: Mapped[float] = mapped_column(Float, nullable=False)
    audio_duration: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Quality metrics
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    has_multiple_speakers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Processing options used
    prompt: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    response_format: Mapped[str] = mapped_column(String(20), default="json", nullable=False)
    
    # Status and workflow
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="transcriptions")
    script: Mapped[Optional["Script"]] = relationship("Script", back_populates="transcription")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_transcriptions_video_id", "video_id"),
        Index("idx_transcriptions_language", "source_language", "detected_language"),
        Index("idx_transcriptions_model", "model_used", "created_at"),
        Index("idx_transcriptions_quality", "confidence_score", "word_count"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="check_confidence_range"),
        CheckConstraint("language_confidence IS NULL OR (language_confidence >= 0 AND language_confidence <= 1)", name="check_language_confidence_range"),
        CheckConstraint("processing_time > 0", name="check_processing_time_positive"),
        CheckConstraint("audio_duration > 0", name="check_audio_duration_positive"),
        CheckConstraint("word_count >= 0", name="check_transcription_word_count_non_negative"),
        CheckConstraint("speaker_count IS NULL OR speaker_count >= 1", name="check_speaker_count_positive"),
        CheckConstraint("temperature >= 0 AND temperature <= 1", name="check_temperature_range"),
    )
    
    def __repr__(self) -> str:
        return f"<Transcription(id={self.id}, video_id={self.video_id}, word_count={self.word_count})>"
    
    @property
    def accuracy_rating(self) -> str:
        """Get human-readable accuracy rating."""
        if self.confidence_score >= 0.9:
            return "Excellent"
        elif self.confidence_score >= 0.8:
            return "Good"
        elif self.confidence_score >= 0.7:
            return "Fair"
        else:
            return "Poor"


class TTSGeneration(Base):
    """Text-to-speech generation model."""
    
    __tablename__ = "tts_generations"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    script_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    
    # Text and voice configuration
    text: Mapped[str] = mapped_column(Text, nullable=False)
    voice_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    voice_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_used: Mapped[str] = mapped_column(String(100), default="eleven_monolingual_v1", nullable=False)
    
    # Voice settings
    voice_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    stability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    similarity_boost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    style_exaggeration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Output configuration
    output_format: Mapped[str] = mapped_column(String(20), default="mp3", nullable=False)
    sample_rate: Mapped[int] = mapped_column(Integer, default=22050, nullable=False)
    quality: Mapped[str] = mapped_column(String(20), default="standard", nullable=False)
    
    # Generated audio information
    audio_file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False)  # Seconds
    audio_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Processing details
    processing_time: Mapped[float] = mapped_column(Float, nullable=False)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False)
    characters_used: Mapped[int] = mapped_column(Integer, nullable=False)  # Billable characters
    
    # Quality and analysis
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-10
    naturalness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-10
    clarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-10
    
    # Status and workflow
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Usage tracking
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    script: Mapped["Script"] = relationship("Script", back_populates="tts_generations")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_tts_generations_script_id", "script_id"),
        Index("idx_tts_generations_voice", "voice_id", "model_used"),
        Index("idx_tts_generations_status", "status", "created_at"),
        Index("idx_tts_generations_quality", "quality_score", "naturalness_score"),
        CheckConstraint("file_size > 0", name="check_tts_file_size_positive"),
        CheckConstraint("duration > 0", name="check_tts_duration_positive"),
        CheckConstraint("processing_time > 0", name="check_tts_processing_time_positive"),
        CheckConstraint("character_count > 0", name="check_tts_character_count_positive"),
        CheckConstraint("characters_used > 0", name="check_tts_characters_used_positive"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 10)", name="check_tts_quality_range"),
        CheckConstraint("naturalness_score IS NULL OR (naturalness_score >= 0 AND naturalness_score <= 10)", name="check_naturalness_range"),
        CheckConstraint("clarity_score IS NULL OR (clarity_score >= 0 AND clarity_score <= 10)", name="check_clarity_range"),
        CheckConstraint("stability IS NULL OR (stability >= 0 AND stability <= 1)", name="check_stability_range"),
        CheckConstraint("similarity_boost IS NULL OR (similarity_boost >= 0 AND similarity_boost <= 1)", name="check_similarity_range"),
        CheckConstraint("sample_rate > 0", name="check_sample_rate_positive"),
        CheckConstraint("download_count >= 0", name="check_download_count_non_negative"),
    )
    
    def __repr__(self) -> str:
        return f"<TTSGeneration(id={self.id}, voice_id={self.voice_id}, duration={self.duration})>"
    
    @property
    def cost_estimate(self) -> float:
        """Estimate cost based on characters used (placeholder calculation)."""
        # This would be based on the actual TTS provider pricing
        cost_per_1k_chars = 0.015  # Example: $0.015 per 1K characters
        return (self.characters_used / 1000) * cost_per_1k_chars


class ContentAnalysis(Base):
    """Content analysis and insights model."""
    
    __tablename__ = "content_analysis"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    script_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Content being analyzed
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_length: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Sentiment analysis
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # positive, negative, neutral, mixed
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)  # -1 to 1
    emotions: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    emotion_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Readability analysis
    readability_score: Mapped[float] = mapped_column(Float, nullable=False)  # Flesch reading ease (0-100)
    complexity_level: Mapped[str] = mapped_column(String(20), nullable=False)  # elementary, middle_school, etc.
    average_sentence_length: Mapped[float] = mapped_column(Float, nullable=False)
    syllable_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Content structure analysis
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    unique_word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    sentence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    paragraph_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Topic and keyword analysis
    key_topics: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    keyword_density: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    named_entities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Language and style analysis
    language_detected: Mapped[str] = mapped_column(String(10), nullable=False)
    formality_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1, higher is more formal
    tone_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    writing_style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Engagement prediction
    engagement_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    virality_potential: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    target_audience_match: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    
    # Content quality metrics
    clarity_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    coherence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    originality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    
    # Processing metadata
    analysis_model: Mapped[str] = mapped_column(String(100), nullable=False)
    processing_time: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    script: Mapped["Script"] = relationship("Script", back_populates="content_analysis")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_content_analysis_sentiment", "sentiment", "sentiment_score"),
        Index("idx_content_analysis_readability", "readability_score", "complexity_level"),
        Index("idx_content_analysis_engagement", "engagement_score", "virality_potential"),
        Index("idx_content_analysis_quality", "clarity_score", "coherence_score"),
        CheckConstraint("sentiment_score >= -1 AND sentiment_score <= 1", name="check_content_sentiment_range"),
        CheckConstraint("readability_score >= 0 AND readability_score <= 100", name="check_content_readability_range"),
        CheckConstraint("formality_score >= 0 AND formality_score <= 1", name="check_formality_range"),
        CheckConstraint("engagement_score IS NULL OR (engagement_score >= 0 AND engagement_score <= 100)", name="check_content_engagement_range"),
        CheckConstraint("virality_potential IS NULL OR (virality_potential >= 0 AND virality_potential <= 100)", name="check_virality_range"),
        CheckConstraint("target_audience_match IS NULL OR (target_audience_match >= 0 AND target_audience_match <= 100)", name="check_audience_match_range"),
        CheckConstraint("clarity_score >= 0 AND clarity_score <= 100", name="check_content_clarity_range"),
        CheckConstraint("coherence_score >= 0 AND coherence_score <= 100", name="check_coherence_range"),
        CheckConstraint("originality_score IS NULL OR (originality_score >= 0 AND originality_score <= 100)", name="check_originality_range"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="check_content_confidence_range"),
        CheckConstraint("content_length > 0", name="check_content_length_positive"),
        CheckConstraint("word_count > 0", name="check_content_word_count_positive"),
        CheckConstraint("unique_word_count > 0", name="check_unique_word_count_positive"),
        CheckConstraint("sentence_count > 0", name="check_sentence_count_positive"),
        CheckConstraint("paragraph_count > 0", name="check_paragraph_count_positive"),
        CheckConstraint("syllable_count > 0", name="check_syllable_count_positive"),
        CheckConstraint("processing_time > 0", name="check_content_processing_time_positive"),
        CheckConstraint("unique_word_count <= word_count", name="check_unique_words_logical"),
    )
    
    def __repr__(self) -> str:
        return f"<ContentAnalysis(script_id={self.script_id}, sentiment={self.sentiment}, readability={self.readability_score})>"
    
    @property
    def overall_quality_score(self) -> float:
        """Calculate overall content quality score."""
        scores = [self.clarity_score, self.coherence_score]
        if self.originality_score:
            scores.append(self.originality_score)
        return sum(scores) / len(scores)