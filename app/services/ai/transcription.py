"""
OpenAI Whisper Transcription Service.

This module provides comprehensive audio transcription capabilities using
OpenAI's Whisper API with support for multiple languages, segmentation,
and intelligent content processing.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, BinaryIO, Tuple
from uuid import UUID

import openai
from openai import AsyncOpenAI
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.exceptions import TranscriptionError, ValidationError as AppValidationError
from app.core.logging import get_logger
from app.models.script import Transcription
from app.schemas.script import (
    TranscriptionCreate, TranscriptionResponse, TranscriptionSegment
)
from app.utils.file_utils import ensure_directory_exists, calculate_file_hash
from app.utils.audio_utils import AudioProcessor

logger = get_logger(__name__)
settings = get_settings()


class TranscriptionService:
    """
    Service for audio transcription using OpenAI Whisper API.
    
    Features:
    - Multi-language support with auto-detection
    - Time-segmented transcription
    - Confidence scoring
    - Audio preprocessing and optimization
    - Caching and deduplication
    - Batch processing capabilities
    """
    
    def __init__(self):
        """Initialize the transcription service."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.audio_processor = AudioProcessor()
        self.supported_languages = {
            "en": "English", "es": "Spanish", "fr": "French", "de": "German",
            "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ja": "Japanese",
            "ko": "Korean", "zh": "Chinese", "ar": "Arabic", "hi": "Hindi",
            "nl": "Dutch", "sv": "Swedish", "pl": "Polish", "tr": "Turkish",
            "cs": "Czech", "da": "Danish", "fi": "Finnish", "no": "Norwegian"
        }
        self.max_file_size = 25 * 1024 * 1024  # 25MB OpenAI limit
        
    async def transcribe_audio(
        self,
        audio_file: BinaryIO,
        language: Optional[str] = None,
        model: str = "whisper-1",
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        response_format: str = "verbose_json",
        timestamp_granularities: List[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using OpenAI Whisper API.
        
        Args:
            audio_file: Audio file binary stream
            language: Target language code (auto-detect if None)
            model: Whisper model to use (whisper-1, whisper-large, etc.)
            prompt: Optional prompt for context
            temperature: Sampling temperature (0.0-1.0)
            response_format: Response format (json, text, srt, verbose_json, vtt)
            timestamp_granularities: Granularity for timestamps (word, segment)
            
        Returns:
            Dict containing transcription results with segments and metadata
            
        Raises:
            TranscriptionError: If transcription fails
            ValidationError: If parameters are invalid
        """
        start_time = time.time()
        
        try:
            # Validate parameters
            await self._validate_transcription_params(
                language, model, temperature, response_format
            )
            
            # Prepare audio file
            audio_file.seek(0)
            file_size = len(audio_file.read())
            audio_file.seek(0)
            
            if file_size > self.max_file_size:
                raise TranscriptionError(
                    f"Audio file too large: {file_size} bytes (max: {self.max_file_size})"
                )
            
            # Set default timestamp granularities
            if timestamp_granularities is None:
                timestamp_granularities = ["segment"]
                if response_format == "verbose_json":
                    timestamp_granularities.append("word")
            
            # Prepare transcription parameters
            transcription_params = {
                "file": audio_file,
                "model": model,
                "response_format": response_format,
                "temperature": temperature,
                "timestamp_granularities": timestamp_granularities
            }
            
            if language:
                transcription_params["language"] = language
            if prompt:
                transcription_params["prompt"] = prompt
                
            logger.info(f"Starting transcription with model {model}, language: {language}")
            
            # Call OpenAI Whisper API
            transcription = await self.client.audio.transcriptions.create(**transcription_params)
            
            # Process response based on format
            if response_format == "verbose_json":
                result = await self._process_verbose_response(transcription)
            else:
                result = await self._process_simple_response(transcription, model, language)
            
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            result["model_used"] = model
            result["file_size"] = file_size
            
            logger.info(f"Transcription completed in {processing_time:.2f}s")
            return result
            
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise TranscriptionError(f"Rate limit exceeded: {e}")
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise TranscriptionError(f"API error: {e}")
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(f"Transcription failed: {e}")
    
    async def transcribe_video_audio(
        self,
        video_path: str,
        language: Optional[str] = None,
        model: str = "whisper-1"
    ) -> Dict[str, Any]:
        """
        Extract audio from video and transcribe it.
        
        Args:
            video_path: Path to video file
            language: Target language code
            model: Whisper model to use
            
        Returns:
            Dict containing transcription results
        """
        try:
            # Extract audio from video
            audio_path = await self.audio_processor.extract_audio_from_video(video_path)
            
            # Optimize audio for transcription
            optimized_audio_path = await self.audio_processor.optimize_for_transcription(audio_path)
            
            # Transcribe the optimized audio
            with open(optimized_audio_path, "rb") as audio_file:
                result = await self.transcribe_audio(
                    audio_file=audio_file,
                    language=language,
                    model=model,
                    response_format="verbose_json"
                )
            
            # Add audio metadata
            audio_info = await self.audio_processor.get_audio_info(optimized_audio_path)
            result.update({
                "audio_duration": audio_info.get("duration", 0),
                "audio_sample_rate": audio_info.get("sample_rate"),
                "audio_channels": audio_info.get("channels"),
                "original_video_path": video_path,
                "extracted_audio_path": optimized_audio_path
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Video audio transcription failed: {e}")
            raise TranscriptionError(f"Video transcription failed: {e}")
    
    async def detect_language(self, audio_file: BinaryIO) -> Tuple[str, float]:
        """
        Detect the language of audio content.
        
        Args:
            audio_file: Audio file binary stream
            
        Returns:
            Tuple of (language_code, confidence)
        """
        try:
            # Use a small sample for language detection
            audio_file.seek(0)
            
            transcription = await self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                temperature=0.0
            )
            
            detected_language = getattr(transcription, 'language', 'en')
            # OpenAI doesn't provide confidence directly, so we estimate based on text quality
            confidence = self._estimate_language_confidence(transcription.text, detected_language)
            
            return detected_language, confidence
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en", 0.5  # Default to English with low confidence
    
    async def transcribe_with_speakers(
        self,
        audio_file: BinaryIO,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio with speaker identification (basic implementation).
        
        Note: OpenAI Whisper doesn't natively support speaker diarization,
        so this is a basic implementation that could be enhanced with
        additional services like pyannote or similar.
        
        Args:
            audio_file: Audio file binary stream
            language: Target language code
            
        Returns:
            Dict containing transcription with speaker segments
        """
        try:
            # Get basic transcription with timestamps
            result = await self.transcribe_audio(
                audio_file=audio_file,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["segment", "word"]
            )
            
            # Basic speaker change detection based on silence gaps
            # This is a simplified approach - production would use dedicated diarization
            enhanced_segments = await self._detect_speaker_changes(result.get("segments", []))
            result["segments_with_speakers"] = enhanced_segments
            result["has_multiple_speakers"] = len(set(seg.get("speaker", 0) for seg in enhanced_segments)) > 1
            result["estimated_speaker_count"] = len(set(seg.get("speaker", 0) for seg in enhanced_segments))
            
            return result
            
        except Exception as e:
            logger.error(f"Speaker transcription failed: {e}")
            raise TranscriptionError(f"Speaker transcription failed: {e}")
    
    async def batch_transcribe(
        self,
        audio_files: List[Tuple[str, BinaryIO]],
        language: Optional[str] = None,
        model: str = "whisper-1",
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Transcribe multiple audio files concurrently.
        
        Args:
            audio_files: List of (filename, file_object) tuples
            language: Target language code
            model: Whisper model to use
            max_concurrent: Maximum concurrent transcriptions
            
        Returns:
            List of transcription results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def transcribe_single(filename: str, audio_file: BinaryIO) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await self.transcribe_audio(
                        audio_file=audio_file,
                        language=language,
                        model=model
                    )
                    result["filename"] = filename
                    return result
                except Exception as e:
                    logger.error(f"Failed to transcribe {filename}: {e}")
                    return {
                        "filename": filename,
                        "error": str(e),
                        "status": "failed"
                    }
        
        tasks = [
            transcribe_single(filename, audio_file)
            for filename, audio_file in audio_files
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch transcription error: {result}")
                processed_results.append({
                    "error": str(result),
                    "status": "failed"
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _validate_transcription_params(
        self,
        language: Optional[str],
        model: str,
        temperature: float,
        response_format: str
    ) -> None:
        """Validate transcription parameters."""
        if language and language not in self.supported_languages:
            raise AppValidationError(f"Unsupported language: {language}")
        
        if not 0.0 <= temperature <= 1.0:
            raise AppValidationError("Temperature must be between 0.0 and 1.0")
        
        allowed_formats = ["json", "text", "srt", "verbose_json", "vtt"]
        if response_format not in allowed_formats:
            raise AppValidationError(f"Invalid response format: {response_format}")
        
        # Add model validation here if needed
        allowed_models = ["whisper-1"]  # Extend as OpenAI adds more models
        if model not in allowed_models:
            logger.warning(f"Using unvalidated model: {model}")
    
    async def _process_verbose_response(self, transcription) -> Dict[str, Any]:
        """Process verbose JSON response from OpenAI Whisper."""
        segments = []
        words = []
        
        # Process segments
        for segment in getattr(transcription, 'segments', []):
            segment_data = {
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "text": segment.get("text", "").strip(),
                "confidence": self._calculate_segment_confidence(segment)
            }
            segments.append(segment_data)
            
            # Extract words if available
            if hasattr(segment, 'words'):
                for word in segment.words:
                    words.append({
                        "start": word.get("start", 0),
                        "end": word.get("end", 0),
                        "word": word.get("word", ""),
                        "confidence": word.get("confidence", 0.9)
                    })
        
        return {
            "text": transcription.text,
            "language": getattr(transcription, 'language', 'en'),
            "duration": getattr(transcription, 'duration', 0),
            "segments": segments,
            "words": words,
            "confidence": self._calculate_overall_confidence(segments),
            "word_count": len(transcription.text.split()),
            "detected_language": getattr(transcription, 'language', 'en')
        }
    
    async def _process_simple_response(
        self,
        transcription,
        model: str,
        language: Optional[str]
    ) -> Dict[str, Any]:
        """Process simple text response from OpenAI Whisper."""
        text = str(transcription) if hasattr(transcription, '__str__') else transcription.text
        
        return {
            "text": text,
            "language": language or "en",
            "duration": 0,  # Not available in simple format
            "segments": [],
            "words": [],
            "confidence": 0.9,  # Default confidence for simple format
            "word_count": len(text.split()),
            "detected_language": language or "en"
        }
    
    def _calculate_segment_confidence(self, segment) -> float:
        """Calculate confidence score for a segment."""
        # OpenAI doesn't provide confidence directly, so we estimate
        # based on segment characteristics
        text = segment.get("text", "")
        duration = segment.get("end", 0) - segment.get("start", 0)
        
        # Factors that might indicate higher confidence
        base_confidence = 0.9
        
        # Penalize very short segments
        if duration < 0.5:
            base_confidence -= 0.1
        
        # Penalize segments with few words
        word_count = len(text.split())
        if word_count < 2:
            base_confidence -= 0.1
        
        # Boost confidence for longer, coherent segments
        if word_count > 5 and duration > 2:
            base_confidence += 0.05
        
        return max(0.1, min(1.0, base_confidence))
    
    def _calculate_overall_confidence(self, segments: List[Dict]) -> float:
        """Calculate overall confidence from segment scores."""
        if not segments:
            return 0.9
        
        confidences = [seg.get("confidence", 0.9) for seg in segments]
        return sum(confidences) / len(confidences)
    
    def _estimate_language_confidence(self, text: str, language: str) -> float:
        """Estimate language detection confidence based on text characteristics."""
        # Simple heuristic based on text length and character patterns
        base_confidence = 0.8
        
        if len(text) > 100:
            base_confidence += 0.1
        
        if len(text) < 20:
            base_confidence -= 0.2
        
        return max(0.1, min(1.0, base_confidence))
    
    async def _detect_speaker_changes(self, segments: List[Dict]) -> List[Dict]:
        """
        Basic speaker change detection based on silence gaps.
        
        This is a simplified implementation. Production systems would use
        specialized speaker diarization services.
        """
        enhanced_segments = []
        current_speaker = 0
        
        for i, segment in enumerate(segments):
            # Simple heuristic: change speaker if there's a significant gap
            if i > 0:
                prev_end = segments[i-1].get("end", 0)
                current_start = segment.get("start", 0)
                gap = current_start - prev_end
                
                # If gap > 2 seconds, might be speaker change
                if gap > 2.0:
                    current_speaker += 1
            
            enhanced_segment = segment.copy()
            enhanced_segment["speaker"] = current_speaker
            enhanced_segments.append(enhanced_segment)
        
        return enhanced_segments


class TranscriptionManager:
    """
    High-level manager for transcription operations with database integration.
    """
    
    def __init__(self, db_session):
        """Initialize with database session."""
        self.db_session = db_session
        self.transcription_service = TranscriptionService()
    
    async def create_transcription(
        self,
        video_id: UUID,
        audio_file_path: str,
        language: Optional[str] = None,
        model: str = "whisper-1"
    ) -> TranscriptionResponse:
        """
        Create a transcription and save to database.
        
        Args:
            video_id: Associated video ID
            audio_file_path: Path to audio file
            language: Target language
            model: Whisper model to use
            
        Returns:
            TranscriptionResponse with created transcription
        """
        try:
            # Transcribe the audio
            with open(audio_file_path, "rb") as audio_file:
                result = await self.transcription_service.transcribe_audio(
                    audio_file=audio_file,
                    language=language,
                    model=model,
                    response_format="verbose_json"
                )
            
            # Create database record
            transcription = Transcription(
                video_id=video_id,
                audio_file_path=audio_file_path,
                source_language=language or result["detected_language"],
                detected_language=result["detected_language"],
                language_confidence=result.get("confidence", 0.9),
                text=result["text"],
                segments={"segments": result["segments"], "words": result.get("words", [])},
                model_used=model,
                processing_time=result["processing_time"],
                audio_duration=result["duration"],
                confidence_score=result["confidence"],
                word_count=result["word_count"],
                has_multiple_speakers=result.get("has_multiple_speakers", False),
                status="completed"
            )
            
            self.db_session.add(transcription)
            await self.db_session.commit()
            await self.db_session.refresh(transcription)
            
            return TranscriptionResponse(
                id=transcription.id,
                text=transcription.text,
                language=transcription.detected_language,
                duration=transcription.audio_duration,
                segments=[
                    TranscriptionSegment(**seg)
                    for seg in result["segments"]
                ],
                confidence=transcription.confidence_score,
                words_count=transcription.word_count,
                processing_time=transcription.processing_time,
                created_at=transcription.created_at
            )
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to create transcription: {e}")
            raise TranscriptionError(f"Failed to create transcription: {e}")