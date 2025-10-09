"""
Batch video ingestion service for processing multiple videos concurrently.

This module provides batch processing capabilities for video ingestion operations.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4

from app.core.logging import get_logger
from app.services.ingest.video_ingestion import VideoIngestionService
from app.services.ingest.url_validator import URLValidator

logger = get_logger(__name__)


class BatchStatus(str, Enum):
    """Batch processing status enumeration."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    """Batch ingestion job data structure."""
    job_id: str
    user_id: str
    urls: List[str]
    options: Dict[str, Any]
    status: BatchStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    total_videos: int = 0
    successful_videos: int = 0
    failed_videos: int = 0
    results: List[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
        self.total_videos = len(self.urls)


class BatchVideoIngestionService:
    """
    Service for batch processing multiple video ingestions.
    """
    
    def __init__(self, max_concurrent: int = 5):
        """Initialize batch video ingestion service."""
        self.ingestion_service = VideoIngestionService()
        self.url_validator = URLValidator()
        self.max_concurrent = max_concurrent
        self.active_jobs: Dict[str, BatchJob] = {}
    
    async def start_batch_ingestion(
        self,
        urls: List[str],
        user_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a batch video ingestion job.
        
        Args:
            urls: List of video URLs to ingest
            user_id: User ID for tracking
            options: Ingestion options
            
        Returns:
            Batch job ID
        """
        job_id = f"batch_{user_id}_{int(datetime.now().timestamp())}"
        
        # Create batch job
        batch_job = BatchJob(
            job_id=job_id,
            user_id=user_id,
            urls=urls,
            options=options or {},
            status=BatchStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.active_jobs[job_id] = batch_job
        
        # Start processing in background
        asyncio.create_task(self._process_batch(batch_job))
        
        logger.info(f"Started batch ingestion job: {job_id} with {len(urls)} URLs")
        return job_id
    
    async def _process_batch(self, batch_job: BatchJob) -> None:
        """Process a batch ingestion job."""
        try:
            batch_job.status = BatchStatus.RUNNING
            batch_job.started_at = datetime.now()
            
            logger.info(f"Processing batch job: {batch_job.job_id}")
            
            # Process URLs with concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def process_single_url(url: str, index: int) -> Dict[str, Any]:
                async with semaphore:
                    try:
                        result = await self.ingestion_service.ingest_video(
                            url=url,
                            user_id=batch_job.user_id,
                            options=batch_job.options
                        )
                        result['batch_job_id'] = batch_job.job_id
                        result['url_index'] = index
                        result['original_url'] = url
                        return result
                    except Exception as e:
                        logger.error(f"Failed to process URL {url}: {str(e)}")
                        return {
                            'success': False,
                            'batch_job_id': batch_job.job_id,
                            'url_index': index,
                            'original_url': url,
                            'error': str(e),
                            'step': 'processing'
                        }
            
            # Create tasks for all URLs
            tasks = [
                asyncio.create_task(process_single_url(url, i))
                for i, url in enumerate(batch_job.urls)
            ]
            
            # Process results as they complete
            for task in asyncio.as_completed(tasks):
                result = await task
                batch_job.results.append(result)
                
                # Update progress
                if result.get('success', False):
                    batch_job.successful_videos += 1
                else:
                    batch_job.failed_videos += 1
                
                processed = batch_job.successful_videos + batch_job.failed_videos
                batch_job.progress = int((processed / batch_job.total_videos) * 100)
                
                logger.info(
                    f"Batch {batch_job.job_id} progress: {processed}/{batch_job.total_videos} "
                    f"({batch_job.progress}%) - Success: {batch_job.successful_videos}, "
                    f"Failed: {batch_job.failed_videos}"
                )
            
            # Mark as completed
            batch_job.status = BatchStatus.COMPLETED
            batch_job.completed_at = datetime.now()
            
            duration = (batch_job.completed_at - batch_job.started_at).total_seconds()
            logger.info(
                f"Batch job {batch_job.job_id} completed in {duration:.2f}s. "
                f"Success: {batch_job.successful_videos}, Failed: {batch_job.failed_videos}"
            )
            
        except asyncio.CancelledError:
            batch_job.status = BatchStatus.CANCELLED
            batch_job.completed_at = datetime.now()
            logger.info(f"Batch job {batch_job.job_id} was cancelled")
            
        except Exception as e:
            batch_job.status = BatchStatus.FAILED
            batch_job.error_message = str(e)
            batch_job.completed_at = datetime.now()
            logger.error(f"Batch job {batch_job.job_id} failed: {str(e)}")
    
    def get_batch_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch ingestion job."""
        if job_id not in self.active_jobs:
            return None
        
        job = self.active_jobs[job_id]
        
        return {
            'job_id': job.job_id,
            'user_id': job.user_id,
            'status': job.status.value,
            'progress': job.progress,
            'total_videos': job.total_videos,
            'successful_videos': job.successful_videos,
            'failed_videos': job.failed_videos,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error_message': job.error_message
        }
    
    def get_batch_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed results of a batch ingestion job."""
        if job_id not in self.active_jobs:
            return None
        
        job = self.active_jobs[job_id]
        
        return {
            'job_id': job.job_id,
            'user_id': job.user_id,
            'status': job.status.value,
            'total_videos': job.total_videos,
            'successful_videos': job.successful_videos,
            'failed_videos': job.failed_videos,
            'success_rate': (job.successful_videos / job.total_videos * 100) if job.total_videos > 0 else 0,
            'results': job.results
        }