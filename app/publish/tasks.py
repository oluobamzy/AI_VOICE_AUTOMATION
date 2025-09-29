from celery import current_task
from app.core.celery_app import celery_app
from app.core.logging import logger
from app.publish.service import publish_service
from app.models.schemas import VideoStatus, PublishConfig


@celery_app.task(bind=True)
def publish_video_task(
    self, 
    video_id: int, 
    video_path: str, 
    publish_config_dict: dict
):
    """Celery task to publish video to platform"""
    try:
        logger.info(f"Starting video publishing for video_id: {video_id}")
        
        # Convert dict to Pydantic model
        publish_config = PublishConfig(**publish_config_dict)
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 30, "total": 100, "status": f"Uploading to {publish_config.platform}..."}
        )
        
        # Publish video
        publish_result = await publish_service.publish_video(
            video_path=video_path,
            publish_config=publish_config
        )
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Verifying upload..."}
        )
        
        # Verify upload status
        status_result = await publish_service.get_upload_status(
            platform=publish_config.platform.value,
            video_id=publish_result["video_id"]
        )
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Publishing complete"}
        )
        
        logger.info(f"Video published successfully for video_id: {video_id}")
        
        return {
            "video_id": video_id,
            "publish_result": publish_result,
            "status_result": status_result,
            "status": VideoStatus.COMPLETED
        }
        
    except Exception as e:
        logger.error(f"Video publishing failed for video_id {video_id}: {e}")
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise


@celery_app.task(bind=True)
def check_upload_status_task(self, video_id: int, platform: str, platform_video_id: str):
    """Celery task to check upload status"""
    try:
        logger.info(f"Checking upload status for video_id: {video_id}")
        
        status_result = await publish_service.get_upload_status(
            platform=platform,
            video_id=platform_video_id
        )
        
        return {
            "video_id": video_id,
            "status_result": status_result,
            "status": VideoStatus.COMPLETED
        }
        
    except Exception as e:
        logger.error(f"Status check failed for video_id {video_id}: {e}")
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise