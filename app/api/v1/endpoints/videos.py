"""
Video processing endpoints.

This module provides endpoints for video ingestion, processing,
and status monitoring.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.db.session import get_async_session
from app.core.logging import get_logger
from app.schemas.video import VideoCreate, VideoResponse, VideoStatusResponse
from app.services.ingest.video_downloader import VideoDownloader
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> VideoResponse:
    """
    Upload a video file for processing.
    
    Args:
        file: The video file to upload
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        VideoResponse: Created video record
        
    Raises:
        HTTPException: If upload fails or file is invalid
    """
    logger.info(f"User {current_user.username} uploading video file: {file.filename}")
    
    # Validate file type and size
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a video"
        )
    
    try:
        # Import Video model
        from app.models.video import Video
        import uuid
        from datetime import datetime
        
        # Use the authenticated user's ID
        user_id = current_user.id
        
        # Create new video record
        video_id = uuid.uuid4()
        video = Video(
            id=video_id,
            user_id=user_id,  # Use existing or newly created user
            title=file.filename or f"Uploaded Video {video_id}",  # Required field
            status="uploaded",
            file_size=file.size if hasattr(file, 'size') else None,
            format=file.content_type.split('/')[-1] if file.content_type else "mp4",
            language="en",  # Required field with default
            tags=[],  # Required field with default
            source_url=None
        )
        
        # Save to database
        db.add(video)
        await db.commit()
        await db.refresh(video)
        
        logger.info(f"Video saved to database with ID: {video_id}")
        
        return VideoResponse(
            id=str(video.id),
            filename=video.title,  # Use title since filename might not be in model
            status=video.status,
            created_at=video.created_at.isoformat(),
            updated_at=video.updated_at.isoformat() if video.updated_at else None,
            source_url=video.source_url,
            file_size=video.file_size,
            duration=video.duration,
            resolution=video.resolution,
            format=video.format,
            description=video.description,
            tags=video.tags or []
        )
        
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading video: {str(e)}"
        )


@router.post("/from-url", response_model=VideoResponse)
async def create_video_from_url(
    video_data: VideoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> VideoResponse:
    """
    Create a video processing job from a URL.
    
    Args:
        video_data: Video creation data including URL
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        VideoResponse: Created video record
        
    Raises:
        HTTPException: If URL is invalid or download fails
    """
    logger.info(f"Creating video from URL: {video_data.source_url}")
    
    try:
        # Import Video model
        from app.models.video import Video
        import uuid
        from datetime import datetime
        
        # For now, create a dummy user_id (in production, this would come from authentication)
        dummy_user_id = uuid.uuid4()
        
        # Create new video record from URL
        video_id = uuid.uuid4()
        video = Video(
            id=video_id,
            user_id=dummy_user_id,  # Required field
            title=f"Video from {video_data.platform}: {video_id}",  # Required field
            status="downloading",
            source_url=str(video_data.source_url),
            source_platform=video_data.platform,
            description=video_data.description,
            language="en",  # Required field with default
            tags=video_data.tags or []  # Required field
        )
        
        # Save to database
        db.add(video)
        await db.commit()
        await db.refresh(video)
        
        logger.info(f"Video from URL saved to database with ID: {video_id}")
        
        return VideoResponse(
            id=str(video.id),
            filename=video.title,  # Use title as filename for response
            status=video.status,
            created_at=video.created_at.isoformat(),
            updated_at=video.updated_at.isoformat() if video.updated_at else None,
            source_url=video.source_url,
            file_size=video.file_size,
            duration=video.duration,
            resolution=video.resolution,
            format=video.format,
            description=video.description,
            tags=video.tags or []
        )
        
    except Exception as e:
        logger.error(f"Error creating video from URL: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating video from URL: {str(e)}"
        )


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(
    video_id: UUID,
    db: AsyncSession = Depends(get_async_session)
) -> VideoStatusResponse:
    """
    Get the processing status of a video.
    
    Args:
        video_id: UUID of the video
        db: Database session
        
    Returns:
        VideoStatusResponse: Current video processing status
        
    Raises:
        HTTPException: If video not found
    """
    logger.info(f"Getting status for video: {video_id}")
    
    # TODO: Implement actual status retrieval
    # This would query the database and task queue status
    
    return VideoStatusResponse(
        id=str(video_id),
        status="processing",
        progress=45,
        current_stage="script_rewriting",
        estimated_completion="2025-09-30T01:00:00Z"
    )


@router.get("/", response_model=List[VideoResponse])
async def list_videos(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> List[VideoResponse]:
    """
    List videos for the current user with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status_filter: Optional status filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[VideoResponse]: List of video records for the user
    """
    logger.info(f"Listing videos for user {current_user.username}: skip={skip}, limit={limit}, status={status_filter}")
    
    try:
        # Import Video model
        from app.models.video import Video
        from sqlalchemy import select
        
        # Build query for current user's videos
        query = select(Video).where(Video.user_id == current_user.id).offset(skip).limit(limit)
        if status_filter:
            query = query.where(Video.status == status_filter)
        
        # Execute query
        result = await db.execute(query)
        videos = result.scalars().all()
        
        # Convert to response models
        return [
            VideoResponse(
                id=str(video.id),
                filename=video.title,  # Use title as filename in response
                status=video.status,
                created_at=video.created_at.isoformat() if video.created_at else None,
                updated_at=video.updated_at.isoformat() if video.updated_at else None,
                source_url=video.source_url,
                file_size=video.file_size,
                duration=video.duration,
                resolution=video.resolution,
                format=video.format,
                description=video.description,
                tags=video.tags or []
            )
            for video in videos
        ]
        
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        # Return empty list if database query fails
        return []


@router.delete("/{video_id}")
async def delete_video(
    video_id: UUID,
    db: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Delete a video and its associated data.
    
    Args:
        video_id: UUID of the video to delete
        db: Database session
        
    Returns:
        dict: Deletion confirmation
        
    Raises:
        HTTPException: If video not found
    """
    logger.info(f"Deleting video: {video_id}")
    
    # TODO: Implement actual video deletion
    # This would:
    # 1. Cancel any running tasks
    # 2. Delete files from storage
    # 3. Remove database records
    
    return {"message": f"Video {video_id} deleted successfully"}


@router.get("/{video_id}/download")
async def download_video(
    video_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Download a processed video file.
    
    Args:
        video_id: UUID of the video to download
        db: Database session
        
    Returns:
        FileResponse: The video file
        
    Raises:
        HTTPException: If video not found or file doesn't exist
    """
    logger.info(f"Downloading video: {video_id}")
    
    try:
        # Import Video model
        from app.models.video import Video
        from sqlalchemy import select
        
        # Get video from database
        query = select(Video).where(Video.id == video_id)
        result = await db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        # Check if processed file exists
        # For now, return the original file path or a placeholder
        file_path = f"/tmp/{video.filename}"  # This would be your actual storage path
        
        if os.path.exists(file_path):
            return FileResponse(
                path=file_path,
                filename=video.filename,
                media_type="video/mp4"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file not found on storage"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error downloading video"
        )


@router.get("/{video_id}/view")
async def view_video(
    video_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get video details and streaming URL.
    
    Args:
        video_id: UUID of the video to view
        db: Database session
        
    Returns:
        dict: Video details with streaming URL
        
    Raises:
        HTTPException: If video not found
    """
    logger.info(f"Getting view details for video: {video_id}")
    
    try:
        # Import Video model
        from app.models.video import Video
        from sqlalchemy import select
        
        # Get video from database
        query = select(Video).where(Video.id == video_id)
        result = await db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        # Extract filename from original_file_path or use title as fallback
        filename = video.title
        if video.original_file_path:
            import os
            filename = os.path.basename(video.original_file_path)
        
        return {
            "id": str(video.id),
            "title": video.title,
            "filename": filename,
            "status": video.status,
            "duration": video.duration,
            "resolution": video.resolution,
            "file_size": video.file_size,
            "format": video.format,
            "streaming_url": f"/api/v1/videos/{video_id}/stream",
            "download_url": f"/api/v1/videos/{video_id}/download",
            "thumbnail_url": f"/api/v1/videos/{video_id}/thumbnail",
            "created_at": video.created_at.isoformat() if video.created_at else None,
            "updated_at": video.updated_at.isoformat() if video.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video details {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting video details"
        )