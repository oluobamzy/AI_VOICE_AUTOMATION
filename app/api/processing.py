from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.models.schemas import VideoProcessingRequest, ProcessingTask
from app.transform.tasks import transform_video_task, apply_filters_task
from app.avatar.tasks import generate_avatar_video_task, generate_script_task
from app.publish.tasks import publish_video_task
from app.core.logging import logger

router = APIRouter(prefix="/processing", tags=["processing"])


@router.post("/transform/{video_id}")
async def start_video_transformation(
    video_id: int,
    platform: str,
    custom_config: dict = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Start video transformation for specific platform"""
    try:
        # In a real implementation, you'd get the video path from the database
        input_path = f"/tmp/videos/video_{video_id}.mp4"  # Placeholder
        
        task = transform_video_task.delay(
            video_id=video_id,
            input_path=input_path,
            platform=platform,
            custom_config=custom_config or {}
        )
        
        logger.info(f"Started transformation task {task.id} for video {video_id}")
        
        return {
            "task_id": task.id,
            "video_id": video_id,
            "platform": platform,
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Error starting transformation for video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start video transformation"
        )


@router.post("/avatar/{video_id}")
async def generate_avatar_video(
    video_id: int,
    processing_request: VideoProcessingRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate avatar video with AI"""
    try:
        # Mock video metadata - in real implementation, get from database
        video_metadata = {
            "duration": 30,
            "resolution": "1080x1920",
            "platform": "tiktok"
        }
        
        task = generate_avatar_video_task.delay(
            video_id=video_id,
            video_metadata=video_metadata,
            avatar_config_dict=processing_request.avatar_config.dict() if processing_request.avatar_config else {},
            custom_script=processing_request.custom_script
        )
        
        logger.info(f"Started avatar generation task {task.id} for video {video_id}")
        
        return {
            "task_id": task.id,
            "video_id": video_id,
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Error starting avatar generation for video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start avatar generation"
        )


@router.post("/publish/{video_id}")
async def publish_video(
    video_id: int,
    processing_request: VideoProcessingRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Publish video to platform"""
    try:
        if not processing_request.publish_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Publish config is required"
            )
        
        # In real implementation, get actual video path from database
        video_path = f"/tmp/videos/processed_video_{video_id}.mp4"
        
        task = publish_video_task.delay(
            video_id=video_id,
            video_path=video_path,
            publish_config_dict=processing_request.publish_config.dict()
        )
        
        logger.info(f"Started publishing task {task.id} for video {video_id}")
        
        return {
            "task_id": task.id,
            "video_id": video_id,
            "platform": processing_request.publish_config.platform,
            "status": "started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting publishing for video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start video publishing"
        )


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of processing task"""
    try:
        from app.core.celery_app import celery_app
        
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == "PENDING":
            response = {
                "task_id": task_id,
                "state": task_result.state,
                "current": 0,
                "total": 100,
                "status": "Task is waiting to be processed"
            }
        elif task_result.state == "PROGRESS":
            response = {
                "task_id": task_id,
                "state": task_result.state,
                "current": task_result.info.get("current", 0),
                "total": task_result.info.get("total", 100),
                "status": task_result.info.get("status", "")
            }
        elif task_result.state == "SUCCESS":
            response = {
                "task_id": task_id,
                "state": task_result.state,
                "current": 100,
                "total": 100,
                "result": task_result.result
            }
        else:  # FAILURE
            response = {
                "task_id": task_id,
                "state": task_result.state,
                "error": str(task_result.info)
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task status"
        )