"""
Publishing tasks.

This module contains Celery tasks for publishing videos to various platforms
including YouTube, TikTok, Instagram, and other social media platforms.
"""

import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta

from celery import Task, group
from celery.exceptions import Retry

from app.tasks.celery_app import celery_app
# Temporarily disable publishing service imports for basic Celery setup
# from app.services.publishing.youtube_publisher import YouTubePublisher
# from app.services.publishing.tiktok_publisher import TikTokPublisher
# from app.services.publishing.instagram_publisher import InstagramPublisher
# from app.services.publishing.twitter_publisher import TwitterPublisher
from app.utils.metadata_processor import MetadataProcessor
from app.core.logging import get_logger

logger = get_logger(__name__)


class PublishingTaskBase(Task):
    """Base task class for publishing operations."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle publishing task failure."""
        logger.error(f"Publishing Task {task_id} failed: {exc}")
        logger.error(f"Platform: {kwargs.get('platform', 'unknown')}")
        logger.error(f"Video ID: {kwargs.get('video_id', 'unknown')}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle publishing task success."""
        logger.info(f"Publishing Task {task_id} completed successfully")
        if isinstance(retval, dict) and 'platform_url' in retval:
            logger.info(f"Published to: {retval['platform_url']}")


@celery_app.task(bind=True, base=PublishingTaskBase, max_retries=3)
def publish_to_youtube_task(
    self,
    video_path: str,
    metadata: Dict[str, Any],
    thumbnail_path: Optional[str] = None,
    schedule_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish video to YouTube.
    
    Args:
        video_path: Path to video file
        metadata: Video metadata (title, description, tags, etc.)
        thumbnail_path: Path to thumbnail image
        schedule_time: ISO format schedule time (optional)
        
    Returns:
        Dict containing publishing results
    """
    try:
        logger.info(f"Starting YouTube publishing task")
        logger.info(f"Video: {video_path}")
        logger.info(f"Title: {metadata.get('title', 'Untitled')}")
        
        youtube_publisher = YouTubePublisher()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                youtube_publisher.upload_video(
                    video_path=video_path,
                    title=metadata.get("title", "Untitled"),
                    description=metadata.get("description", ""),
                    tags=metadata.get("tags", []),
                    category_id=metadata.get("category_id", "22"),  # People & Blogs
                    privacy_status=metadata.get("privacy_status", "public"),
                    thumbnail_path=thumbnail_path,
                    schedule_time=schedule_time
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"YouTube publishing failed: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 120 * (2 ** self.request.retries)  # Start with 2min delay
            logger.info(f"Retrying YouTube upload in {countdown} seconds")
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=PublishingTaskBase, max_retries=3)
def publish_to_tiktok_task(
    self,
    video_path: str,
    metadata: Dict[str, Any],
    schedule_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish video to TikTok.
    
    Args:
        video_path: Path to video file
        metadata: Video metadata (caption, hashtags, etc.)
        schedule_time: ISO format schedule time (optional)
        
    Returns:
        Dict containing publishing results
    """
    try:
        logger.info(f"Starting TikTok publishing task")
        logger.info(f"Video: {video_path}")
        logger.info(f"Caption: {metadata.get('caption', '')[:50]}...")
        
        tiktok_publisher = TikTokPublisher()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                tiktok_publisher.upload_video(
                    video_path=video_path,
                    caption=metadata.get("caption", ""),
                    hashtags=metadata.get("hashtags", []),
                    privacy_level=metadata.get("privacy_level", "PUBLIC_TO_EVERYONE"),
                    disable_duet=metadata.get("disable_duet", False),
                    disable_comment=metadata.get("disable_comment", False),
                    disable_stitch=metadata.get("disable_stitch", False),
                    schedule_time=schedule_time
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"TikTok publishing failed: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            countdown = 90 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=PublishingTaskBase, max_retries=3)
def publish_to_instagram_task(
    self,
    video_path: str,
    metadata: Dict[str, Any],
    cover_image_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish video to Instagram (Reels).
    
    Args:
        video_path: Path to video file
        metadata: Video metadata (caption, hashtags, etc.)
        cover_image_path: Path to cover image
        
    Returns:
        Dict containing publishing results
    """
    try:
        logger.info(f"Starting Instagram publishing task")
        logger.info(f"Video: {video_path}")
        
        instagram_publisher = InstagramPublisher()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                instagram_publisher.upload_reel(
                    video_path=video_path,
                    caption=metadata.get("caption", ""),
                    hashtags=metadata.get("hashtags", []),
                    location_id=metadata.get("location_id"),
                    cover_image_path=cover_image_path,
                    share_to_feed=metadata.get("share_to_feed", True)
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Instagram publishing failed: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=PublishingTaskBase, max_retries=2)
def publish_to_twitter_task(
    self,
    video_path: str,
    metadata: Dict[str, Any],
    thread_mode: bool = False
) -> Dict[str, Any]:
    """
    Publish video to Twitter/X.
    
    Args:
        video_path: Path to video file
        metadata: Video metadata (text, hashtags, etc.)
        thread_mode: Whether to create a thread for long content
        
    Returns:
        Dict containing publishing results
    """
    try:
        logger.info(f"Starting Twitter publishing task")
        logger.info(f"Video: {video_path}")
        
        twitter_publisher = TwitterPublisher()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                twitter_publisher.post_video(
                    video_path=video_path,
                    text=metadata.get("text", ""),
                    hashtags=metadata.get("hashtags", []),
                    thread_mode=thread_mode,
                    sensitive_content=metadata.get("sensitive_content", False)
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Twitter publishing failed: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            countdown = 45 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=PublishingTaskBase)
def optimize_metadata_for_platform_task(
    self,
    original_metadata: Dict[str, Any],
    platform: str,
    content_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Optimize metadata for specific platform.
    
    Args:
        original_metadata: Original video metadata
        platform: Target platform (youtube, tiktok, instagram, twitter)
        content_analysis: AI content analysis results
        
    Returns:
        Dict containing platform-optimized metadata
    """
    try:
        logger.info(f"Optimizing metadata for platform: {platform}")
        
        metadata_processor = MetadataProcessor()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                metadata_processor.optimize_for_platform(
                    metadata=original_metadata,
                    platform=platform,
                    content_analysis=content_analysis
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Metadata optimization failed: {str(exc)}")
        raise exc


@celery_app.task(bind=True, base=PublishingTaskBase)
def schedule_publishing_task(
    self,
    video_id: str,
    platforms: List[str],
    publishing_schedule: Dict[str, str],
    metadata_per_platform: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Schedule publishing to multiple platforms.
    
    Args:
        video_id: Video identifier
        platforms: List of platforms to publish to
        publishing_schedule: Schedule times per platform
        metadata_per_platform: Optimized metadata for each platform
        
    Returns:
        Dict containing scheduled task IDs
    """
    try:
        logger.info(f"Scheduling publishing for video: {video_id}")
        logger.info(f"Platforms: {platforms}")
        
        scheduled_tasks = {}
        
        for platform in platforms:
            schedule_time = publishing_schedule.get(platform)
            metadata = metadata_per_platform.get(platform, {})
            
            if not schedule_time:
                logger.warning(f"No schedule time for platform: {platform}")
                continue
            
            # Convert schedule time to ETA for Celery
            schedule_dt = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
            eta = schedule_dt
            
            # Schedule appropriate publishing task
            if platform == "youtube":
                task = publish_to_youtube_task.apply_async(
                    kwargs={
                        "video_path": metadata.get("video_path"),
                        "metadata": metadata,
                        "thumbnail_path": metadata.get("thumbnail_path"),
                        "schedule_time": schedule_time
                    },
                    eta=eta
                )
            elif platform == "tiktok":
                task = publish_to_tiktok_task.apply_async(
                    kwargs={
                        "video_path": metadata.get("video_path"),
                        "metadata": metadata,
                        "schedule_time": schedule_time
                    },
                    eta=eta
                )
            elif platform == "instagram":
                task = publish_to_instagram_task.apply_async(
                    kwargs={
                        "video_path": metadata.get("video_path"),
                        "metadata": metadata,
                        "cover_image_path": metadata.get("cover_image_path")
                    },
                    eta=eta
                )
            elif platform == "twitter":
                task = publish_to_twitter_task.apply_async(
                    kwargs={
                        "video_path": metadata.get("video_path"),
                        "metadata": metadata,
                        "thread_mode": metadata.get("thread_mode", False)
                    },
                    eta=eta
                )
            else:
                logger.warning(f"Unknown platform: {platform}")
                continue
            
            scheduled_tasks[platform] = {
                "task_id": task.id,
                "scheduled_time": schedule_time,
                "platform": platform
            }
        
        return {
            "success": True,
            "video_id": video_id,
            "scheduled_tasks": scheduled_tasks,
            "total_platforms": len(scheduled_tasks)
        }
        
    except Exception as exc:
        logger.error(f"Publishing scheduling failed: {str(exc)}")
        raise exc


@celery_app.task(bind=True, base=PublishingTaskBase)
def publish_to_all_platforms_task(
    self,
    video_id: str,
    video_path: str,
    platforms: List[str],
    metadata_per_platform: Dict[str, Dict[str, Any]]
) -> str:
    """
    Publish video to all specified platforms simultaneously.
    
    Args:
        video_id: Video identifier
        video_path: Path to video file
        platforms: List of platforms to publish to
        metadata_per_platform: Platform-specific metadata
        
    Returns:
        Group job ID for tracking all publishing tasks
    """
    try:
        logger.info(f"Starting multi-platform publishing for video: {video_id}")
        logger.info(f"Platforms: {platforms}")
        
        # Create parallel publishing tasks
        publishing_tasks = []
        
        for platform in platforms:
            metadata = metadata_per_platform.get(platform, {})
            metadata["video_path"] = video_path
            
            if platform == "youtube":
                task = publish_to_youtube_task.s(
                    video_path=video_path,
                    metadata=metadata,
                    thumbnail_path=metadata.get("thumbnail_path")
                )
            elif platform == "tiktok":
                task = publish_to_tiktok_task.s(
                    video_path=video_path,
                    metadata=metadata
                )
            elif platform == "instagram":
                task = publish_to_instagram_task.s(
                    video_path=video_path,
                    metadata=metadata,
                    cover_image_path=metadata.get("cover_image_path")
                )
            elif platform == "twitter":
                task = publish_to_twitter_task.s(
                    video_path=video_path,
                    metadata=metadata,
                    thread_mode=metadata.get("thread_mode", False)
                )
            else:
                logger.warning(f"Unknown platform: {platform}")
                continue
            
            publishing_tasks.append(task)
        
        # Execute all publishing tasks in parallel
        if publishing_tasks:
            job = group(publishing_tasks).apply_async()
            return job.id
        else:
            raise ValueError("No valid platforms specified for publishing")
        
    except Exception as exc:
        logger.error(f"Multi-platform publishing failed: {str(exc)}")
        raise exc


@celery_app.task(bind=True, base=PublishingTaskBase)
def monitor_publishing_status_task(
    self,
    job_id: str,
    platforms: List[str],
    check_interval: int = 30
) -> Dict[str, Any]:
    """
    Monitor publishing status across platforms.
    
    Args:
        job_id: Publishing job ID to monitor
        platforms: List of platforms being published to
        check_interval: Status check interval in seconds
        
    Returns:
        Dict containing publishing status for all platforms
    """
    try:
        logger.info(f"Monitoring publishing status for job: {job_id}")
        
        # TODO: Implement actual monitoring logic
        # This would check the status of all publishing tasks
        # and provide real-time updates on publishing progress
        
        return {
            "job_id": job_id,
            "status": "monitoring",
            "platforms": platforms,
            "last_check": datetime.utcnow().isoformat(),
            "overall_status": "in_progress"
        }
        
    except Exception as exc:
        logger.error(f"Publishing monitoring failed: {str(exc)}")
        raise exc


@celery_app.task
def cleanup_published_files_task(
    retention_days: int = 7
) -> Dict[str, Any]:
    """
    Clean up published video files after retention period.
    
    Args:
        retention_days: Number of days to retain files
        
    Returns:
        Dict containing cleanup results
    """
    try:
        logger.info(f"Starting cleanup of published files older than {retention_days} days")
        
        # TODO: Implement actual cleanup logic
        # This would clean up old published video files, thumbnails, etc.
        # based on retention policies
        
        return {
            "success": True,
            "files_cleaned": 0,
            "space_freed": 0,
            "retention_days": retention_days
        }
        
    except Exception as exc:
        logger.error(f"Published files cleanup failed: {str(exc)}")
        raise exc