from celery import current_task
from app.core.celery_app import celery_app
from app.core.logging import logger
from app.transform.service import video_transformer
from app.models.schemas import VideoStatus


@celery_app.task(bind=True)
def transform_video_task(self, video_id: int, input_path: str, platform: str, custom_config: dict = None):
    """Celery task to transform video for specific platform"""
    try:
        logger.info(f"Starting video transformation for video_id: {video_id}, platform: {platform}")
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Starting transformation..."}
        )
        
        # Transform video for platform
        transformed_path = video_transformer.transform_for_platform(
            input_path=input_path,
            platform=platform,
            custom_config=custom_config
        )
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Optimizing for streaming..."}
        )
        
        # Optimize for streaming
        optimized_path = video_transformer.optimize_for_streaming(transformed_path)
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Transformation complete"}
        )
        
        logger.info(f"Video transformation completed for video_id: {video_id}")
        
        return {
            "video_id": video_id,
            "transformed_path": optimized_path,
            "platform": platform,
            "status": VideoStatus.COMPLETED
        }
        
    except Exception as e:
        logger.error(f"Video transformation failed for video_id {video_id}: {e}")
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise


@celery_app.task(bind=True) 
def apply_filters_task(self, video_id: int, input_path: str, filters: dict):
    """Celery task to apply filters to video"""
    try:
        logger.info(f"Applying filters to video_id: {video_id}")
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Applying filters..."}
        )
        
        filtered_path = video_transformer.apply_filters(input_path, filters)
        
        current_task.update_state(
            state="PROGRESS", 
            meta={"current": 100, "total": 100, "status": "Filters applied"}
        )
        
        return {
            "video_id": video_id,
            "filtered_path": filtered_path,
            "status": VideoStatus.COMPLETED
        }
        
    except Exception as e:
        logger.error(f"Filter application failed for video_id {video_id}: {e}")
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise