from celery import current_task
from app.core.celery_app import celery_app
from app.core.logging import logger
from app.avatar.service import avatar_service
from app.models.schemas import VideoStatus, AvatarConfig


@celery_app.task(bind=True)
def generate_avatar_video_task(
    self, 
    video_id: int, 
    video_metadata: dict, 
    avatar_config_dict: dict,
    custom_script: str = None,
    background_video_path: str = None
):
    """Celery task to generate avatar video with AI"""
    try:
        logger.info(f"Starting avatar generation for video_id: {video_id}")
        
        # Convert dict to Pydantic model
        avatar_config = AvatarConfig(**avatar_config_dict)
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Generating script..."}
        )
        
        # Generate script if not provided
        if not custom_script:
            script = await avatar_service.generate_script(
                video_metadata=video_metadata,
                custom_prompt=None
            )
        else:
            script = custom_script
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 60, "total": 100, "status": "Creating avatar video..."}
        )
        
        # Create avatar video
        avatar_video_path = await avatar_service.create_avatar_video(
            script=script,
            avatar_config=avatar_config,
            background_video_path=background_video_path
        )
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Avatar generation complete"}
        )
        
        logger.info(f"Avatar generation completed for video_id: {video_id}")
        
        return {
            "video_id": video_id,
            "avatar_video_path": avatar_video_path,
            "script": script,
            "status": VideoStatus.COMPLETED
        }
        
    except Exception as e:
        logger.error(f"Avatar generation failed for video_id {video_id}: {e}")
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise


@celery_app.task(bind=True)
def generate_script_task(self, video_id: int, video_metadata: dict, custom_prompt: str = None):
    """Celery task to generate script using AI"""
    try:
        logger.info(f"Generating script for video_id: {video_id}")
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Generating script..."}
        )
        
        script = await avatar_service.generate_script(
            video_metadata=video_metadata,
            custom_prompt=custom_prompt
        )
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Script generation complete"}
        )
        
        return {
            "video_id": video_id,
            "script": script,
            "status": VideoStatus.COMPLETED
        }
        
    except Exception as e:
        logger.error(f"Script generation failed for video_id {video_id}: {e}")
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise