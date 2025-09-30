"""
Script and content transformation Pydantic schemas.

This module defines schemas for script processing, AI content transformation,
transcription, and text-to-speech operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator, HttpUrl


class TranscriptionBase(BaseModel):
    """Base transcription schema."""
    language: str = Field(default="en", description="Language code for transcription")
    audio_file_path: str = Field(..., description="Path to audio file")
    
    @validator("language")
    def validate_language(cls, v):
        # Common language codes supported by Whisper
        supported_languages = [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", 
            "ar", "hi", "nl", "sv", "pl", "tr", "cs", "da", "fi", "no"
        ]
        if v not in supported_languages:
            raise ValueError(f"Language must be one of: {', '.join(supported_languages)}")
        return v


class TranscriptionCreate(TranscriptionBase):
    """Schema for creating a transcription job."""
    video_id: Optional[UUID] = Field(None, description="Associated video ID")
    model: str = Field(default="whisper-1", description="Transcription model to use")
    prompt: Optional[str] = Field(None, max_length=500, description="Optional prompt for context")
    temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="Sampling temperature")
    
    @validator("model")
    def validate_model(cls, v):
        allowed_models = ["whisper-1", "whisper-large", "whisper-base"]
        if v not in allowed_models:
            raise ValueError(f"Model must be one of: {', '.join(allowed_models)}")
        return v


class TranscriptionSegment(BaseModel):
    """Schema for transcription time segments."""
    start: float = Field(..., ge=0, description="Start time in seconds")
    end: float = Field(..., ge=0, description="End time in seconds")
    text: str = Field(..., description="Transcribed text for this segment")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")
    
    @validator("end")
    def validate_end_after_start(cls, v, values):
        if 'start' in values and v <= values['start']:
            raise ValueError("End time must be after start time")
        return v


class TranscriptionResponse(BaseModel):
    """Schema for transcription results."""
    id: UUID = Field(..., description="Transcription ID")
    text: str = Field(..., description="Full transcribed text")
    language: str = Field(..., description="Detected/specified language")
    duration: float = Field(..., ge=0, description="Audio duration in seconds")
    segments: List[TranscriptionSegment] = Field(default_factory=list, description="Time-segmented transcription")
    confidence: float = Field(..., ge=0, le=1, description="Overall confidence score")
    words_count: int = Field(..., ge=0, description="Number of words transcribed")
    processing_time: float = Field(..., ge=0, description="Processing time in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class ScriptBase(BaseModel):
    """Base script schema."""
    title: Optional[str] = Field(None, max_length=200, description="Script title")
    content: str = Field(..., min_length=1, description="Script content")
    language: str = Field(default="en", description="Script language")
    
    @validator("content")
    def validate_content_length(cls, v):
        if len(v.strip()) == 0:
            raise ValueError("Script content cannot be empty")
        if len(v) > 10000:  # 10k character limit
            raise ValueError("Script content too long (max 10,000 characters)")
        return v.strip()


class ScriptCreate(ScriptBase):
    """Schema for creating a script."""
    video_id: Optional[UUID] = Field(None, description="Associated video ID")
    transcription_id: Optional[UUID] = Field(None, description="Source transcription ID")
    tags: List[str] = Field(default_factory=list, max_items=20, description="Script tags")


class ScriptRewriteRequest(BaseModel):
    """Schema for script rewriting request."""
    original_script: str = Field(..., min_length=1, description="Original script to rewrite")
    style: str = Field(default="engaging", description="Writing style")
    target_audience: str = Field(default="general", description="Target audience")
    tone: str = Field(default="friendly", description="Tone of voice")
    length_preference: str = Field(default="maintain", description="Length preference")
    keywords: List[str] = Field(default_factory=list, max_items=10, description="Keywords to include")
    avoid_words: List[str] = Field(default_factory=list, max_items=10, description="Words to avoid")
    custom_instructions: Optional[str] = Field(None, max_length=500, description="Custom rewriting instructions")
    
    @validator("style")
    def validate_style(cls, v):
        allowed_styles = [
            "engaging", "professional", "casual", "educational", "entertaining",
            "persuasive", "informative", "conversational", "formal", "creative"
        ]
        if v not in allowed_styles:
            raise ValueError(f"Style must be one of: {', '.join(allowed_styles)}")
        return v
    
    @validator("target_audience")
    def validate_audience(cls, v):
        allowed_audiences = [
            "general", "teens", "young_adults", "adults", "seniors",
            "professionals", "students", "entrepreneurs", "creators", "technical"
        ]
        if v not in allowed_audiences:
            raise ValueError(f"Target audience must be one of: {', '.join(allowed_audiences)}")
        return v
    
    @validator("tone")
    def validate_tone(cls, v):
        allowed_tones = [
            "friendly", "professional", "humorous", "serious", "inspirational",
            "authoritative", "empathetic", "excited", "calm", "urgent"
        ]
        if v not in allowed_tones:
            raise ValueError(f"Tone must be one of: {', '.join(allowed_tones)}")
        return v
    
    @validator("length_preference")
    def validate_length(cls, v):
        allowed_lengths = ["shorter", "maintain", "longer", "specific"]
        if v not in allowed_lengths:
            raise ValueError(f"Length preference must be one of: {', '.join(allowed_lengths)}")
        return v


class ScriptRewriteResponse(BaseModel):
    """Schema for script rewriting results."""
    id: UUID = Field(..., description="Rewrite job ID")
    original_script: str = Field(..., description="Original script")
    rewritten_script: str = Field(..., description="Rewritten script")
    style: str = Field(..., description="Applied writing style")
    target_audience: str = Field(..., description="Target audience")
    tone: str = Field(..., description="Applied tone")
    original_word_count: int = Field(..., ge=0, description="Original word count")
    rewritten_word_count: int = Field(..., ge=0, description="Rewritten word count")
    estimated_reading_time: float = Field(..., ge=0, description="Estimated reading time in minutes")
    changes_summary: str = Field(..., description="Summary of changes made")
    quality_score: float = Field(..., ge=0, le=10, description="Quality score (1-10)")
    processing_time: float = Field(..., ge=0, description="Processing time in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class ScriptResponse(BaseModel):
    """Schema for script response data."""
    id: UUID = Field(..., description="Script ID")
    title: Optional[str] = Field(None, description="Script title")
    content: str = Field(..., description="Script content")
    language: str = Field(..., description="Script language")
    word_count: int = Field(..., ge=0, description="Word count")
    estimated_reading_time: float = Field(..., ge=0, description="Estimated reading time in minutes")
    tags: List[str] = Field(default_factory=list, description="Script tags")
    video_id: Optional[UUID] = Field(None, description="Associated video ID")
    transcription_id: Optional[UUID] = Field(None, description="Source transcription ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class TTSRequest(BaseModel):
    """Schema for text-to-speech request."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice_id: str = Field(..., description="Voice model identifier")
    voice_settings: Optional[Dict[str, Any]] = Field(None, description="Voice generation settings")
    model: str = Field(default="eleven_monolingual_v1", description="TTS model to use")
    output_format: str = Field(default="mp3", description="Output audio format")
    
    @validator("text")
    def validate_text_content(cls, v):
        if len(v.strip()) == 0:
            raise ValueError("Text cannot be empty")
        # Remove excessive whitespace
        return ' '.join(v.split())
    
    @validator("output_format")
    def validate_output_format(cls, v):
        allowed_formats = ["mp3", "wav", "ogg", "flac"]
        if v not in allowed_formats:
            raise ValueError(f"Output format must be one of: {', '.join(allowed_formats)}")
        return v


class TTSResponse(BaseModel):
    """Schema for text-to-speech results."""
    id: UUID = Field(..., description="TTS job ID")
    audio_file_path: str = Field(..., description="Generated audio file path")
    audio_url: Optional[str] = Field(None, description="Public URL to audio file")
    voice_id: str = Field(..., description="Voice model used")
    model: str = Field(..., description="TTS model used")
    text: str = Field(..., description="Original text")
    duration: float = Field(..., ge=0, description="Audio duration in seconds")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    format: str = Field(..., description="Audio format")
    sample_rate: int = Field(..., gt=0, description="Sample rate in Hz")
    quality: str = Field(..., description="Audio quality")
    processing_time: float = Field(..., ge=0, description="Processing time in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class ContentAnalysis(BaseModel):
    """Schema for content analysis results."""
    id: UUID = Field(..., description="Analysis ID")
    content: str = Field(..., description="Analyzed content")
    sentiment: str = Field(..., description="Overall sentiment")
    sentiment_score: float = Field(..., ge=-1, le=1, description="Sentiment score (-1 to 1)")
    emotions: List[str] = Field(default_factory=list, description="Detected emotions")
    key_topics: List[str] = Field(default_factory=list, description="Key topics identified")
    readability_score: float = Field(..., ge=0, le=100, description="Readability score")
    complexity_level: str = Field(..., description="Content complexity level")
    word_count: int = Field(..., ge=0, description="Word count")
    unique_words: int = Field(..., ge=0, description="Unique word count")
    average_sentence_length: float = Field(..., ge=0, description="Average sentence length")
    created_at: datetime = Field(..., description="Analysis timestamp")
    
    @validator("sentiment")
    def validate_sentiment(cls, v):
        allowed_sentiments = ["positive", "negative", "neutral", "mixed"]
        if v not in allowed_sentiments:
            raise ValueError(f"Sentiment must be one of: {', '.join(allowed_sentiments)}")
        return v
    
    @validator("complexity_level")
    def validate_complexity(cls, v):
        allowed_levels = ["elementary", "middle_school", "high_school", "college", "graduate"]
        if v not in allowed_levels:
            raise ValueError(f"Complexity level must be one of: {', '.join(allowed_levels)}")
        return v
    
    class Config:
        from_attributes = True


class HashtagGeneration(BaseModel):
    """Schema for hashtag generation."""
    content: str = Field(..., description="Content to analyze for hashtags")
    max_hashtags: int = Field(default=10, ge=1, le=30, description="Maximum hashtags to generate")
    platform: str = Field(default="general", description="Target platform")
    include_trending: bool = Field(default=True, description="Include trending hashtags")
    
    @validator("platform")
    def validate_platform(cls, v):
        allowed_platforms = ["general", "instagram", "tiktok", "twitter", "youtube", "linkedin"]
        if v not in allowed_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(allowed_platforms)}")
        return v


class HashtagResponse(BaseModel):
    """Schema for hashtag generation results."""
    hashtags: List[str] = Field(..., description="Generated hashtags")
    trending_hashtags: List[str] = Field(default_factory=list, description="Trending hashtags included")
    relevance_scores: Dict[str, float] = Field(default_factory=dict, description="Hashtag relevance scores")
    platform: str = Field(..., description="Target platform")
    created_at: datetime = Field(..., description="Generation timestamp")
    
    class Config:
        from_attributes = True