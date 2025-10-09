"""
Workflow orchestration tasks.

This module contains Celery tasks for orchestrating complex workflows
that combine video processing, AI operations, and publishing tasks.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from celery import Task, group, chain, chord, signature
from celery.exceptions import Retry

from app.tasks.celery_app import celery_app
from app.tasks.video_tasks import (
    download_video_task,
    process_video_task,
    extract_audio_task,
    add_subtitles_task,
    upload_to_storage_task
)
from app.tasks.ai_tasks import (
    transcribe_audio_task,
    generate_script_task,
    synthesize_voice_task,
    generate_avatar_video_task,
    analyze_content_sentiment_task
)
# Temporarily disable publishing task imports for basic Celery setup
# from app.tasks.publishing_tasks import (
#     publish_to_youtube_task,
#     publish_to_tiktok_task,
#     publish_to_instagram_task,
#     publish_to_twitter_task,
#     optimize_metadata_for_platform_task,
#     publish_to_all_platforms_task
# )
from app.core.logging import get_logger
from app.db.session import get_async_session  # Fixed import path
from app.models.video import Video
from app.models.job import Job

logger = get_logger(__name__)


class WorkflowTaskBase(Task):
    """Base task class for workflow orchestration."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle workflow task failure."""
        logger.error(f"Workflow Task {task_id} failed: {exc}")
        logger.error(f"Workflow: {kwargs.get('workflow_type', 'unknown')}")
        logger.error(f"Step: {kwargs.get('current_step', 'unknown')}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle workflow task success."""
        logger.info(f"Workflow Task {task_id} completed successfully")
        if isinstance(retval, dict) and 'workflow_id' in retval:
            logger.info(f"Workflow ID: {retval['workflow_id']}")


@celery_app.task(bind=True, base=WorkflowTaskBase)
def complete_video_automation_workflow(
    self,
    source_url: str,
    target_platforms: List[str],
    workflow_config: Dict[str, Any],
    user_id: str
) -> str:
    """
    Complete video automation workflow from URL to published videos.
    
    This is the main orchestration task that coordinates the entire
    video automation pipeline.
    
    Args:
        source_url: Source video URL (TikTok, YouTube, etc.)
        target_platforms: List of platforms to publish to
        workflow_config: Configuration for the entire workflow
        user_id: User identifier
        
    Returns:
        Workflow job ID for tracking
    """
    try:
        logger.info(f"Starting complete video automation workflow")
        logger.info(f"Source URL: {source_url}")
        logger.info(f"Target platforms: {target_platforms}")
        
        # Step 1: Download and process video
        download_chain = chain(
            download_video_task.s(
                url=source_url,
                options=workflow_config.get("download_options", {})
            ),
            extract_audio_task.s()  # Uses result from download_video_task
        )
        
        # Step 2: AI processing (parallel)
        ai_processing_group = group([
            transcribe_audio_task.s(),
            analyze_content_sentiment_task.s()
        ])
        
        # Step 3: Content generation based on AI results
        content_generation_callback = generate_optimized_content.s(
            target_platforms=target_platforms,
            workflow_config=workflow_config,
            user_id=user_id
        )
        
        # Create the complete workflow
        workflow = chain(
            download_chain,
            chord(ai_processing_group, content_generation_callback)
        )
        
        # Execute the workflow
        workflow_job = workflow.apply_async()
        
        # Store workflow job ID for tracking
        # TODO: Store in database for persistent tracking
        
        return workflow_job.id
        
    except Exception as exc:
        logger.error(f"Workflow creation failed: {str(exc)}")
        raise exc


@celery_app.task(bind=True, base=WorkflowTaskBase)
def generate_optimized_content(
    self,
    ai_results: List[Dict[str, Any]],
    target_platforms: List[str],
    workflow_config: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """
    Generate optimized content for target platforms.
    
    Args:
        ai_results: Results from AI processing tasks
        target_platforms: List of platforms to optimize for
        workflow_config: Workflow configuration
        user_id: User identifier
        
    Returns:
        Dict containing content generation results
    """
    try:
        logger.info(f"Starting content generation for platforms: {target_platforms}")
        
        # Extract AI results
        transcription_result = ai_results[0] if ai_results else {}
        sentiment_result = ai_results[1] if len(ai_results) > 1 else {}
        
        transcript = transcription_result.get("transcript", "")
        
        if not transcript:
            raise ValueError("No transcript available for content generation")
        
        # Generate platform-specific scripts
        script_generation_tasks = []
        for platform in target_platforms:
            script_task = generate_script_task.s(
                transcript=transcript,
                target_platform=platform,
                style_preferences=workflow_config.get("style_preferences", {}),
                duration_target=workflow_config.get("duration_targets", {}).get(platform)
            )
            script_generation_tasks.append(script_task)
        
        # Execute script generation in parallel
        script_job = group(script_generation_tasks).apply_async()
        script_results = script_job.get()
        
        # Create platform-specific content
        content_creation_tasks = []
        for i, platform in enumerate(target_platforms):
            script_result = script_results[i] if i < len(script_results) else {}
            script_text = script_result.get("script", "")
            
            if script_text and workflow_config.get("generate_voice", True):
                voice_task = synthesize_voice_task.s(
                    text=script_text,
                    voice_id=workflow_config.get("voice_settings", {}).get("voice_id", "default"),
                    output_path=f"/tmp/voice_{platform}_{user_id}.mp3",
                    voice_settings=workflow_config.get("voice_settings", {})
                )
                content_creation_tasks.append(voice_task)
        
        # Execute content creation
        if content_creation_tasks:
            content_job = group(content_creation_tasks).apply_async()
            content_results = content_job.get()
        else:
            content_results = []
        
        # Trigger final publishing workflow
        publishing_task = publish_generated_content.delay(
            platform_scripts=dict(zip(target_platforms, script_results)),
            voice_results=content_results,
            original_video_path=workflow_config.get("original_video_path"),
            workflow_config=workflow_config,
            user_id=user_id
        )
        
        return {
            "success": True,
            "platforms": target_platforms,
            "script_generation": script_results,
            "content_creation": content_results,
            "publishing_task_id": publishing_task.id,
            "user_id": user_id
        }
        
    except Exception as exc:
        logger.error(f"Content generation failed: {str(exc)}")
        raise exc


@celery_app.task(bind=True, base=WorkflowTaskBase)
def publish_generated_content(
    self,
    platform_scripts: Dict[str, Dict[str, Any]],
    voice_results: List[Dict[str, Any]],
    original_video_path: str,
    workflow_config: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """
    Publish generated content to all target platforms.
    
    Args:
        platform_scripts: Generated scripts per platform
        voice_results: Voice synthesis results
        original_video_path: Path to original processed video
        workflow_config: Workflow configuration
        user_id: User identifier
        
    Returns:
        Dict containing publishing results
    """
    try:
        logger.info(f"Starting content publishing for user: {user_id}")
        
        # Prepare metadata for each platform
        metadata_per_platform = {}
        
        for platform, script_data in platform_scripts.items():
            # Optimize metadata for each platform
            optimization_task = optimize_metadata_for_platform_task.delay(
                original_metadata={
                    "title": script_data.get("title", ""),
                    "description": script_data.get("description", ""),
                    "tags": script_data.get("tags", []),
                    "caption": script_data.get("caption", ""),
                    "hashtags": script_data.get("hashtags", [])
                },
                platform=platform,
                content_analysis=script_data.get("analysis", {})
            )
            
            metadata_per_platform[platform] = optimization_task.get()
        
        # Check if we should schedule or publish immediately
        publish_schedule = workflow_config.get("publish_schedule", {})
        
        if publish_schedule:
            # Schedule publishing
            scheduling_task = schedule_publishing_task.delay(
                video_id=f"workflow_{user_id}_{datetime.utcnow().timestamp()}",
                platforms=list(platform_scripts.keys()),
                publishing_schedule=publish_schedule,
                metadata_per_platform=metadata_per_platform
            )
            
            return {
                "success": True,
                "mode": "scheduled",
                "scheduling_task_id": scheduling_task.id,
                "platforms": list(platform_scripts.keys()),
                "user_id": user_id
            }
        else:
            # Publish immediately
            publishing_job = publish_to_all_platforms_task.delay(
                video_id=f"workflow_{user_id}_{datetime.utcnow().timestamp()}",
                video_path=original_video_path,
                platforms=list(platform_scripts.keys()),
                metadata_per_platform=metadata_per_platform
            )
            
            return {
                "success": True,
                "mode": "immediate",
                "publishing_job_id": publishing_job,
                "platforms": list(platform_scripts.keys()),
                "user_id": user_id
            }
        
    except Exception as exc:
        logger.error(f"Content publishing failed: {str(exc)}")
        raise exc


@celery_app.task(bind=True, base=WorkflowTaskBase, max_retries=2)
def tiktok_to_youtube_shorts_workflow(
    self,
    tiktok_url: str,
    user_id: str,
    customization_options: Optional[Dict[str, Any]] = None
) -> str:
    """
    Specialized workflow for converting TikTok videos to YouTube Shorts.
    
    Args:
        tiktok_url: TikTok video URL
        user_id: User identifier
        customization_options: Optional customization settings
        
    Returns:
        Workflow job ID
    """
    try:
        logger.info(f"Starting TikTok to YouTube Shorts workflow")
        logger.info(f"TikTok URL: {tiktok_url}")
        
        # Default configuration for TikTok to YouTube Shorts
        workflow_config = {
            "download_options": {
                "format": "best[height<=1080]",
                "extract_flat": False
            },
            "target_platforms": ["youtube"],
            "style_preferences": {
                "tone": "engaging",
                "length": "short",
                "include_call_to_action": True
            },
            "duration_targets": {
                "youtube": 60  # YouTube Shorts max 60 seconds
            },
            "generate_voice": customization_options.get("generate_voice", False),
            "voice_settings": customization_options.get("voice_settings", {}),
            "publish_schedule": customization_options.get("publish_schedule", {})
        }
        
        # Merge custom options
        if customization_options:
            workflow_config.update(customization_options)
        
        # Start the complete workflow
        workflow_job = complete_video_automation_workflow.delay(
            source_url=tiktok_url,
            target_platforms=["youtube"],
            workflow_config=workflow_config,
            user_id=user_id
        )
        
        return workflow_job
        
    except Exception as exc:
        logger.error(f"TikTok to YouTube Shorts workflow failed: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        
        raise exc


@celery_app.task(bind=True, base=WorkflowTaskBase)
def bulk_video_processing_workflow(
    self,
    video_urls: List[str],
    target_platforms: List[str],
    workflow_config: Dict[str, Any],
    user_id: str,
    batch_size: int = 5
) -> List[str]:
    """
    Process multiple videos in batches.
    
    Args:
        video_urls: List of video URLs to process
        target_platforms: List of target platforms
        workflow_config: Workflow configuration
        user_id: User identifier
        batch_size: Number of videos to process simultaneously
        
    Returns:
        List of workflow job IDs
    """
    try:
        logger.info(f"Starting bulk video processing for {len(video_urls)} videos")
        logger.info(f"Batch size: {batch_size}")
        
        workflow_jobs = []
        
        # Process videos in batches
        for i in range(0, len(video_urls), batch_size):
            batch_urls = video_urls[i:i + batch_size]
            batch_tasks = []
            
            for url in batch_urls:
                task = complete_video_automation_workflow.s(
                    source_url=url,
                    target_platforms=target_platforms,
                    workflow_config=workflow_config,
                    user_id=user_id
                )
                batch_tasks.append(task)
            
            # Execute batch in parallel
            batch_job = group(batch_tasks).apply_async()
            workflow_jobs.append(batch_job.id)
            
            # Add delay between batches to avoid rate limiting
            if i + batch_size < len(video_urls):
                logger.info(f"Processed batch {i//batch_size + 1}, waiting before next batch...")
                import time
                time.sleep(30)  # 30 second delay between batches
        
        return workflow_jobs
        
    except Exception as exc:
        logger.error(f"Bulk video processing failed: {str(exc)}")
        raise exc


@celery_app.task(bind=True, base=WorkflowTaskBase)
def workflow_status_monitor(
    self,
    workflow_job_id: str,
    user_id: str,
    max_wait_time: int = 3600  # 1 hour
) -> Dict[str, Any]:
    """
    Monitor workflow status and provide updates.
    
    Args:
        workflow_job_id: Workflow job ID to monitor
        user_id: User identifier
        max_wait_time: Maximum time to wait for completion
        
    Returns:
        Dict containing final workflow status
    """
    try:
        logger.info(f"Monitoring workflow: {workflow_job_id}")
        
        # TODO: Implement actual workflow monitoring
        # This would track the progress of complex workflows
        # and provide real-time status updates
        
        return {
            "workflow_id": workflow_job_id,
            "user_id": user_id,
            "status": "monitoring",
            "progress": "0%",
            "current_step": "initialization",
            "estimated_completion": None
        }
        
    except Exception as exc:
        logger.error(f"Workflow monitoring failed: {str(exc)}")
        raise exc


@celery_app.task
def cleanup_workflow_artifacts(
    workflow_id: str,
    cleanup_after_days: int = 7
) -> Dict[str, Any]:
    """
    Clean up temporary files and artifacts from completed workflows.
    
    Args:
        workflow_id: Workflow identifier
        cleanup_after_days: Days after completion to cleanup
        
    Returns:
        Dict containing cleanup results
    """
    try:
        logger.info(f"Cleaning up workflow artifacts: {workflow_id}")
        
        # TODO: Implement actual cleanup logic
        # This would clean up temporary files, intermediate results, etc.
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "files_cleaned": 0,
            "space_freed": 0
        }
        
    except Exception as exc:
        logger.error(f"Workflow cleanup failed: {str(exc)}")
        raise exc