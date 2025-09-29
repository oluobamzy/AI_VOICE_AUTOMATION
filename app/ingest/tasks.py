from celery import current_task
from app.core.celery_app import celery_app
from app.core.logging import logger
from app.ingest.service import video_ingester
from app.models.schemas import VideoStatus


@celery_app.task(bind=True)
def ingest_video_task(self, video_id: int, source_url: str):
    """Celery task to ingest video from source URL"""
    try:
        logger.info(f"Starting video ingestion for video_id: {video_id}")
        
        # Update task progress
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Downloading video..."}
        )
        
        # Download video
        video_path = video_ingester.download_video(source_url)
        
        current_task.update_state(
            state="PROGRESS", 
            meta={"current": 50, "total": 100, "status": "Validating video..."}
        )
        
        # Validate video
        validation_result = video_ingester.validate_video(video_path)
        if not validation_result["valid"]:
            raise Exception(f"Video validation failed: {validation_result['error']}")
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Extracting metadata..."}
        )
        
        # Extract metadata
        metadata = video_ingester.extract_metadata(video_path, source_url)
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Ingestion complete"}
        )
        
        logger.info(f"Video ingestion completed for video_id: {video_id}")
        
        return {
            "video_id": video_id,
            "video_path": video_path,
            "metadata": metadata,
            "status": VideoStatus.COMPLETED
        }
        
    except Exception as e:
        logger.error(f"Video ingestion failed for video_id {video_id}: {e}")
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise