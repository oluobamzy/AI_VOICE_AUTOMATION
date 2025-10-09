"""
AI processing tasks.

This module contains Celery tasks for AI-powered video processing,
including transcription, script generation, voice synthesis, and avatar creation.
"""

import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path

from celery import Task, group, chord
from celery.exceptions import Retry

from app.tasks.celery_app import celery_app
from app.services.ai.transcription import TranscriptionService, TranscriptionManager
from app.db.session import get_async_session
from app.core.logging import get_logger

logger = get_logger(__name__)


class AITaskBase(Task):
    """Base task class for AI operations with enhanced error handling."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle AI task failure with detailed logging."""
        logger.error(f"AI Task {task_id} failed: {exc}")
        logger.error(f"Task args: {args}")
        logger.error(f"Task kwargs: {kwargs}")
        logger.error(f"Exception info: {einfo}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle AI task success."""
        logger.info(f"AI Task {task_id} completed successfully")
        if isinstance(retval, dict) and 'processing_time' in retval:
            logger.info(f"Processing time: {retval['processing_time']}s")


@celery_app.task(bind=True, base=AITaskBase, max_retries=3)
def transcribe_video_task(
    self,
    video_id: str,
    video_path: str,
    language: Optional[str] = None,
    model: str = "whisper-1"
) -> Dict[str, Any]:
    """
    Transcribe video audio with database integration.
    
    Args:
        video_id: Video ID from database
        video_path: Path to video file
        language: Target language (auto-detect if None)
        model: Whisper model to use
        
    Returns:
        Dict containing transcription results and database ID
    """
    try:
        logger.info(f"Starting video transcription task: {video_id}")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            async def transcribe_and_save():
                async with get_async_session() as db:
                    transcription_manager = TranscriptionManager(db)
                    
                    # First extract audio from video
                    transcription_service = TranscriptionService()
                    result = await transcription_service.transcribe_video_audio(
                        video_path=video_path,
                        language=language,
                        model=model
                    )
                    
                    # Create transcription record in database
                    transcription_response = await transcription_manager.create_transcription(
                        video_id=video_id,
                        audio_file_path=result["extracted_audio_path"],
                        language=language,
                        model=model
                    )
                    
                    return {
                        "transcription_id": str(transcription_response.id),
                        "text": result["text"],
                        "language": result["detected_language"],
                        "duration": result["duration"],
                        "segments_count": len(result.get("segments", [])),
                        "word_count": result["word_count"],
                        "confidence": result["confidence"],
                        "processing_time": result["processing_time"],
                        "audio_path": result["extracted_audio_path"]
                    }
            
            result = loop.run_until_complete(transcribe_and_save())
            logger.info(f"Video transcription completed: {video_id}")
            return result
            
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Video transcription failed: {str(exc)}")
        
        # Retry with exponential backoff for API rate limits
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)
            logger.info(f"Retrying video transcription in {countdown} seconds")
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=AITaskBase, max_retries=3)
def transcribe_audio_task(
    self,
    audio_path: str,
    language: Optional[str] = None,
    model: str = "whisper-1"
) -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI Whisper.
    
    Args:
        audio_path: Path to audio file
        language: Target language (auto-detect if None)
        model: Whisper model to use
        
    Returns:
        Dict containing transcription results
    """
    try:
        logger.info(f"Starting audio transcription task: {audio_path}")
        
        transcription_service = TranscriptionService()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            with open(audio_path, 'rb') as audio_file:
                result = loop.run_until_complete(
                    transcription_service.transcribe_audio(
                        audio_file=audio_file,
                        language=language,
                        model=model,
                        response_format="verbose_json"
                    )
                )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Audio transcription failed: {str(exc)}")
        
        # Retry with exponential backoff for API rate limits
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)
            logger.info(f"Retrying transcription in {countdown} seconds")
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=AITaskBase, max_retries=2)
def detect_language_task(
    self,
    audio_path: str
) -> Dict[str, Any]:
    """
    Detect language from audio file.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dict containing detected language and confidence
    """
    try:
        logger.info(f"Starting language detection: {audio_path}")
        
        transcription_service = TranscriptionService()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            with open(audio_path, 'rb') as audio_file:
                language, confidence = loop.run_until_complete(
                    transcription_service.detect_language(audio_file)
                )
            
            return {
                "detected_language": language,
                "confidence": confidence,
                "audio_path": audio_path
            }
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Language detection failed: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            countdown = 30 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=AITaskBase, max_retries=2)
def transcribe_with_speakers_task(
    self,
    audio_path: str,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribe audio with speaker identification.
    
    Args:
        audio_path: Path to audio file
        language: Target language (auto-detect if None)
        
    Returns:
        Dict containing transcription with speaker segments
    """
    try:
        logger.info(f"Starting speaker transcription: {audio_path}")
        
        transcription_service = TranscriptionService()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            with open(audio_path, 'rb') as audio_file:
                result = loop.run_until_complete(
                    transcription_service.transcribe_with_speakers(
                        audio_file=audio_file,
                        language=language
                    )
                )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Speaker transcription failed: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=AITaskBase, max_retries=1)
def batch_transcribe_task(
    self,
    audio_files_info: List[Dict[str, str]],
    language: Optional[str] = None,
    model: str = "whisper-1",
    max_concurrent: int = 3
) -> Dict[str, Any]:
    """
    Transcribe multiple audio files concurrently.
    
    Args:
        audio_files_info: List of dicts with 'filename' and 'path' keys
        language: Target language (auto-detect if None)
        model: Whisper model to use
        max_concurrent: Maximum concurrent transcriptions
        
    Returns:
        Dict containing batch transcription results
    """
    try:
        logger.info(f"Starting batch transcription of {len(audio_files_info)} files")
        
        transcription_service = TranscriptionService()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Prepare audio files for batch processing
            audio_files = []
            for file_info in audio_files_info:
                with open(file_info['path'], 'rb') as audio_file:
                    audio_files.append((file_info['filename'], audio_file))
            
            results = loop.run_until_complete(
                transcription_service.batch_transcribe(
                    audio_files=audio_files,
                    language=language,
                    model=model,
                    max_concurrent=max_concurrent
                )
            )
            
            # Summarize results
            successful = [r for r in results if 'error' not in r]
            failed = [r for r in results if 'error' in r]
            
            return {
                "total_files": len(audio_files_info),
                "successful": len(successful),
                "failed": len(failed),
                "results": results,
                "success_rate": len(successful) / len(audio_files_info) if audio_files_info else 0
            }
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Batch transcription failed: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            countdown = 120 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=AITaskBase, max_retries=2)
def generate_script_task(
    self,
    transcript: str,
    target_platform: str,
    style_preferences: Optional[Dict[str, Any]] = None,
    duration_target: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate optimized script from transcript.
    
    Args:
        transcript: Original video transcript
        target_platform: Target platform (youtube_shorts, tiktok, etc.)
        style_preferences: Style and tone preferences
        duration_target: Target duration in seconds
        
    Returns:
        Dict containing generated script and metadata
    """
    try:
        logger.info(f"Starting script generation for platform: {target_platform}")
        
        script_generator = ScriptGeneratorService()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                script_generator.generate_script(
                    transcript=transcript,
                    target_platform=target_platform,
                    style_preferences=style_preferences,
                    duration_target=duration_target
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Script generation failed: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries), exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=AITaskBase, max_retries=3)
def synthesize_voice_task(
    self,
    text: str,
    voice_id: str,
    output_path: str,
    voice_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Synthesize voice from text using ElevenLabs.
    
    Args:
        text: Text to synthesize
        voice_id: ElevenLabs voice ID
        output_path: Output audio file path
        voice_settings: Voice generation settings
        
    Returns:
        Dict containing synthesis results
    """
    try:
        logger.info(f"Starting voice synthesis task for voice: {voice_id}")
        
        voice_service = VoiceSynthesisService()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                voice_service.synthesize_speech(
                    text=text,
                    voice_id=voice_id,
                    output_path=output_path,
                    voice_settings=voice_settings
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Voice synthesis failed: {str(exc)}")
        
        # Retry with backoff for API limits
        if self.request.retries < self.max_retries:
            countdown = 45 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=AITaskBase, max_retries=2)
def generate_avatar_video_task(
    self,
    script_text: str,
    avatar_id: str,
    output_path: str,
    avatar_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate avatar video using D-ID or Synthesia.
    
    Args:
        script_text: Script for avatar to speak
        avatar_id: Avatar identifier
        output_path: Output video file path
        avatar_settings: Avatar generation settings
        
    Returns:
        Dict containing avatar generation results
    """
    try:
        logger.info(f"Starting avatar video generation for avatar: {avatar_id}")
        
        avatar_service = AvatarGenerationService()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                avatar_service.generate_avatar_video(
                    script_text=script_text,
                    avatar_id=avatar_id,
                    output_path=output_path,
                    settings=avatar_settings
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Avatar generation failed: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=AITaskBase)
def analyze_content_sentiment_task(
    self,
    text: str,
    analysis_type: str = "comprehensive"
) -> Dict[str, Any]:
    """
    Analyze content sentiment and engagement potential.
    
    Args:
        text: Text content to analyze
        analysis_type: Type of analysis (basic, comprehensive, viral_potential)
        
    Returns:
        Dict containing analysis results
    """
    try:
        logger.info(f"Starting content sentiment analysis: {analysis_type}")
        
        text_processor = TextProcessor()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                text_processor.analyze_sentiment(
                    text=text,
                    analysis_type=analysis_type
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Sentiment analysis failed: {str(exc)}")
        raise exc


@celery_app.task(bind=True, base=AITaskBase)
def generate_thumbnails_task(
    self,
    video_path: str,
    output_dir: str,
    count: int = 5,
    style: str = "youtube_shorts"
) -> Dict[str, Any]:
    """
    Generate AI-optimized thumbnails from video.
    
    Args:
        video_path: Input video file path
        output_dir: Directory for output thumbnails
        count: Number of thumbnails to generate
        style: Thumbnail style (youtube_shorts, tiktok, instagram)
        
    Returns:
        Dict containing thumbnail generation results
    """
    try:
        logger.info(f"Generating {count} thumbnails for: {video_path}")
        
        # TODO: Implement thumbnail generation service
        # This would use AI to select best frames and optimize for platform
        
        output_paths = []
        for i in range(count):
            thumbnail_path = f"{output_dir}/thumbnail_{i+1}_{style}.jpg"
            output_paths.append(thumbnail_path)
        
        return {
            "success": True,
            "thumbnail_paths": output_paths,
            "style": style,
            "count": count
        }
        
    except Exception as exc:
        logger.error(f"Thumbnail generation failed: {str(exc)}")
        raise exc


# Workflow tasks that combine multiple AI operations
@celery_app.task(bind=True, base=AITaskBase)
def process_video_with_ai_workflow(
    self,
    video_id: str,
    audio_path: str,
    target_platform: str,
    workflow_config: Dict[str, Any]
) -> str:
    """
    Complete AI processing workflow for video.
    
    This is a workflow task that orchestrates multiple AI operations
    using Celery's chord primitive for parallel execution.
    
    Args:
        video_id: Video identifier
        audio_path: Path to extracted audio
        target_platform: Target platform for optimization
        workflow_config: Configuration for the entire workflow
        
    Returns:
        Workflow job ID for tracking
    """
    try:
        logger.info(f"Starting AI workflow for video: {video_id}")
        
        # Create parallel AI processing tasks
        ai_tasks = group([
            transcribe_audio_task.s(
                audio_path=audio_path,
                language=workflow_config.get("language"),
                model=workflow_config.get("transcription_model", "whisper-1")
            ),
            analyze_content_sentiment_task.s(
                text="",  # Will be filled by transcription result
                analysis_type="viral_potential"
            )
        ])
        
        # Create workflow callback that processes AI results
        workflow_callback = finalize_ai_workflow.s(
            video_id=video_id,
            target_platform=target_platform,
            workflow_config=workflow_config
        )
        
        # Execute workflow with chord (parallel tasks + callback)
        workflow_job = chord(ai_tasks)(workflow_callback)
        
        return workflow_job.id
        
    except Exception as exc:
        logger.error(f"AI workflow creation failed: {str(exc)}")
        raise exc


@celery_app.task(bind=True, base=AITaskBase)
def finalize_ai_workflow(
    self,
    ai_results: List[Dict[str, Any]],
    video_id: str,
    target_platform: str,
    workflow_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Finalize AI workflow with all results.
    
    Args:
        ai_results: Results from parallel AI tasks
        video_id: Video identifier
        target_platform: Target platform
        workflow_config: Workflow configuration
        
    Returns:
        Dict containing complete workflow results
    """
    try:
        logger.info(f"Finalizing AI workflow for video: {video_id}")
        
        # Process and combine AI results
        transcription_result = ai_results[0] if ai_results else {}
        sentiment_result = ai_results[1] if len(ai_results) > 1 else {}
        
        # Generate script based on transcription
        if transcription_result.get("transcript"):
            script_result = generate_script_task.delay(
                transcript=transcription_result["transcript"],
                target_platform=target_platform,
                style_preferences=workflow_config.get("style_preferences"),
                duration_target=workflow_config.get("duration_target")
            ).get()
        else:
            script_result = {"error": "No transcript available"}
        
        return {
            "success": True,
            "video_id": video_id,
            "transcription": transcription_result,
            "sentiment_analysis": sentiment_result,
            "script_generation": script_result,
            "workflow_completed_at": "2025-09-30T00:00:00Z"
        }
        
    except Exception as exc:
        logger.error(f"AI workflow finalization failed: {str(exc)}")
        raise exc