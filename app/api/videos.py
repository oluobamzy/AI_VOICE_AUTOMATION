from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.session import get_db_session
from app.models.schemas import Video, VideoCreate, VideoUpdate, VideoProcessingRequest
from app.models.database import VideoModel
from app.ingest.tasks import ingest_video_task
from app.core.logging import logger

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/", response_model=Video, status_code=status.HTTP_201_CREATED)
async def create_video(
    video_data: VideoCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new video entry and start ingestion"""
    try:
        # Create video record
        db_video = VideoModel(
            title=video_data.title,
            description=video_data.description,
            source_url=str(video_data.source_url),
            platform=video_data.platform,
            tags=video_data.tags
        )
        
        db.add(db_video)
        await db.commit()
        await db.refresh(db_video)
        
        # Start async ingestion task
        task = ingest_video_task.delay(
            video_id=db_video.id,
            source_url=str(video_data.source_url)
        )
        
        logger.info(f"Video created with ID: {db_video.id}, ingestion task: {task.id}")
        
        return Video.from_orm(db_video)
        
    except Exception as e:
        logger.error(f"Error creating video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create video"
        )


@router.get("/", response_model=List[Video])
async def list_videos(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """List all videos with pagination"""
    try:
        from sqlalchemy import select
        
        query = select(VideoModel).offset(skip).limit(limit)
        result = await db.execute(query)
        videos = result.scalars().all()
        
        return [Video.from_orm(video) for video in videos]
        
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list videos"
        )


@router.get("/{video_id}", response_model=Video)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get video by ID"""
    try:
        from sqlalchemy import select
        
        query = select(VideoModel).where(VideoModel.id == video_id)
        result = await db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        return Video.from_orm(video)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get video"
        )


@router.put("/{video_id}", response_model=Video)
async def update_video(
    video_id: int,
    video_update: VideoUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update video by ID"""
    try:
        from sqlalchemy import select
        
        query = select(VideoModel).where(VideoModel.id == video_id)
        result = await db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        # Update fields
        update_data = video_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(video, field, value)
        
        await db.commit()
        await db.refresh(video)
        
        return Video.from_orm(video)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update video"
        )


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete video by ID"""
    try:
        from sqlalchemy import select
        
        query = select(VideoModel).where(VideoModel.id == video_id)
        result = await db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        await db.delete(video)
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete video"
        )