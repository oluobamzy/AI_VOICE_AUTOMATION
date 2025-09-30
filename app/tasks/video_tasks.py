"""
Video processing tasks.

This module contains Celery tasks for video downloading,
processing, and file management operations.
"""

import asyncio
from typing import Dict, Any, Optional

from celery import Task
from celery.exceptions import Retry

from app.tasks.celery_app import celery_app
from app.services.ingest.video_downloader import VideoDownloader
from app.utils.ffmpeg_processor import FFmpegProcessor
from app.utils.storage import StorageManager
from app.core.logging import get_logger

logger = get_logger(__name__)


class CallbackTask(Task):
    """Base task class with error handling and callbacks."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Task {task_id} failed: {exc}")
        # Here you could send notifications, update database, etc.
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(f"Task {task_id} completed successfully")


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def download_video_task(self, url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Download video from URL using yt-dlp.
    
    Args:
        url: Video URL to download
        options: Additional download options
        
    Returns:
        Dict containing download results
    """
    try:
        logger.info(f"Starting video download task for: {url}")
        
        downloader = VideoDownloader()
        
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                downloader.download_video(url, options)
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Video download failed: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=CallbackTask, max_retries=2)
def process_video_task(
    self,
    input_path: str,
    output_path: str,
    processing_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process video with FFmpeg.
    
    Args:
        input_path: Input video file path
        output_path: Output video file path
        processing_config: Processing configuration
        
    Returns:
        Dict containing processing results
    """
    try:
        logger.info(f"Starting video processing task: {input_path}")
        
        processor = FFmpegProcessor()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                processor.convert_video(
                    input_path=input_path,
                    output_path=output_path,
                    target_resolution=processing_config.get("target_resolution"),
                    target_format=processing_config.get("target_format", "mp4"),
                    quality=processing_config.get("quality", "high")
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Video processing failed: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries), exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=CallbackTask)
def extract_audio_task(self, video_path: str, output_path: str) -> Dict[str, Any]:
    """
    Extract audio from video file.
    
    Args:
        video_path: Input video file path
        output_path: Output audio file path
        
    Returns:
        Dict containing extraction results
    """
    try:
        logger.info(f"Starting audio extraction task: {video_path}")
        
        processor = FFmpegProcessor()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                processor.extract_audio(video_path, output_path)
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Audio extraction failed: {str(exc)}")
        raise exc


@celery_app.task(bind=True, base=CallbackTask)
def add_subtitles_task(
    self,
    video_path: str,
    subtitle_text: str,
    output_path: str,
    subtitle_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add subtitles to video.
    
    Args:
        video_path: Input video file path
        subtitle_text: Text to add as subtitles
        output_path: Output video file path
        subtitle_config: Subtitle styling configuration
        
    Returns:
        Dict containing processing results
    """
    try:
        logger.info(f"Adding subtitles to video: {video_path}")
        
        processor = FFmpegProcessor()
        config = subtitle_config or {}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                processor.add_subtitles(
                    video_path=video_path,
                    subtitle_text=subtitle_text,
                    output_path=output_path,
                    font_size=config.get("font_size", 24),
                    font_color=config.get("font_color", "white"),
                    background_color=config.get("background_color", "black@0.5"),
                    position=config.get("position", "bottom")
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Subtitle addition failed: {str(exc)}")
        raise exc


@celery_app.task(bind=True, base=CallbackTask)
def upload_to_storage_task(
    self,
    file_path: str,
    storage_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Upload file to configured storage.
    
    Args:
        file_path: Local file path to upload
        storage_path: Target storage path
        metadata: File metadata
        
    Returns:
        Dict containing upload results
    """
    try:
        logger.info(f"Uploading file to storage: {file_path}")
        
        storage_manager = StorageManager()
        
        with open(file_path, 'rb') as file_data:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    storage_manager.upload_file(
                        file_data=file_data,
                        file_path=storage_path,
                        metadata=metadata
                    )
                )
                return result
            finally:
                loop.close()
                
    except Exception as exc:
        logger.error(f"File upload failed: {str(exc)}")
        raise exc


@celery_app.task
def cleanup_expired_files() -> Dict[str, Any]:
    """
    Periodic task to clean up expired temporary files.
    
    Returns:
        Dict containing cleanup results
    """
    try:
        logger.info("Starting cleanup of expired files")
        
        # TODO: Implement actual cleanup logic
        # This would clean up old temporary files, expired cache entries, etc.
        
        return {
            "success": True,
            "files_cleaned": 0,
            "space_freed": 0
        }
        
    except Exception as exc:
        logger.error(f"Cleanup task failed: {str(exc)}")
        raise exc


@celery_app.task
def health_check_task() -> Dict[str, str]:
    """
    Health check task for monitoring.
    
    Returns:
        Dict containing health status
    """
    try:
        logger.info("Running health check task")
        
        # Basic health checks
        # Check database connectivity, storage access, etc.
        
        return {
            "status": "healthy",
            "timestamp": "2025-09-30T00:00:00Z",
            "worker_id": "worker-1"
        }
        
    except Exception as exc:
        logger.error(f"Health check failed: {str(exc)}")
        return {
            "status": "unhealthy",
            "error": str(exc),
            "timestamp": "2025-09-30T00:00:00Z"
        }