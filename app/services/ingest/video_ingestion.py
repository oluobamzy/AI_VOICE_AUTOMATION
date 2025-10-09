"""
Video ingestion service for handling video URL downloads and processing.

This module provides a comprehensive video ingestion service that handles
URL validation, metadata extraction, video downloading, and storage management.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.video import VideoMetadata
from app.services.ingest.video_downloader import VideoDownloader
from app.services.ingest.url_validator import URLValidator
from app.utils.file_utils import ensure_directory, safe_filename

logger = get_logger(__name__)


class VideoIngestionService:
    """
    Service for ingesting videos from various platforms.
    
    Handles the complete workflow of video ingestion including:
    - URL validation
    - Metadata extraction
    - Video downloading
    - File organization and storage
    """
    
    def __init__(self):
        """Initialize the video ingestion service."""
        self.downloader = VideoDownloader()
        self.validator = URLValidator()
        
        # Storage directories
        self.storage_dir = Path(settings.MEDIA_DIR) / "videos"
        self.temp_dir = Path(settings.MEDIA_DIR) / "temp"
        self.thumbnails_dir = Path(settings.MEDIA_DIR) / "thumbnails"
        
        # Ensure directories exist
        ensure_directory(self.storage_dir)
        ensure_directory(self.temp_dir)
        ensure_directory(self.thumbnails_dir)
        
        # Supported platforms configuration
        self.supported_platforms = {
            'tiktok': {
                'domains': ['tiktok.com', 'vm.tiktok.com'],
                'max_duration': 600  # 10 minutes
            },
            'youtube': {
                'domains': ['youtube.com', 'youtu.be', 'youtube-nocookie.com'],
                'max_duration': 1800  # 30 minutes for shorts
            },
            'instagram': {
                'domains': ['instagram.com', 'instagr.am'],
                'max_duration': 300  # 5 minutes
            },
            'twitter': {
                'domains': ['twitter.com', 'x.com', 't.co'],
                'max_duration': 600  # 10 minutes
            }
        }
    
    async def ingest_video(self, url: str, user_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete video ingestion workflow.
        
        Args:
            url: Video URL to ingest
            user_id: User ID requesting the ingestion
            options: Optional ingestion settings
            
        Returns:
            Dict containing ingestion results
        """
        ingestion_id = str(uuid4())
        logger.info(f"Starting video ingestion: {ingestion_id} for user: {user_id}")
        
        try:
            # Step 1: Validate URL
            validation_result = await self.validate_url(url)
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'ingestion_id': ingestion_id,
                    'error': validation_result['error'],
                    'step': 'url_validation',
                    'user_id': user_id
                }
            
            # Step 2: Extract metadata
            metadata = await self.extract_metadata(url)
            if not metadata:
                return {
                    'success': False,
                    'ingestion_id': ingestion_id,
                    'error': 'Failed to extract video metadata',
                    'step': 'metadata_extraction',
                    'user_id': user_id
                }
            
            # Step 3: Validate content
            content_validation = await self.validate_content(metadata, options)
            if not content_validation['is_valid']:
                return {
                    'success': False,
                    'ingestion_id': ingestion_id,
                    'error': content_validation['error'],
                    'step': 'content_validation',
                    'user_id': user_id,
                    'metadata': metadata.dict()
                }
            
            # Step 4: Download video
            download_result = await self.download_video(url, user_id, options)
            if not download_result['success']:
                return {
                    'success': False,
                    'ingestion_id': ingestion_id,
                    'error': download_result['error'],
                    'step': 'video_download',
                    'user_id': user_id,
                    'metadata': metadata.dict()
                }
            
            # Step 5: Process and store
            storage_result = await self.process_and_store(
                download_result['file_path'], 
                metadata, 
                user_id, 
                ingestion_id
            )
            if not storage_result['success']:
                return {
                    'success': False,
                    'ingestion_id': ingestion_id,
                    'error': storage_result['error'],
                    'step': 'video_storage',
                    'user_id': user_id,
                    'metadata': metadata.dict()
                }
            
            # Step 6: Download thumbnail (optional)
            thumbnail_path = await self.download_thumbnail(url, ingestion_id)
            
            # Compile successful result
            result = {
                'success': True,
                'ingestion_id': ingestion_id,
                'video_path': storage_result['video_path'],
                'metadata': metadata.dict(),
                'file_info': storage_result['file_info'],
                'thumbnail_path': thumbnail_path,
                'user_id': user_id,
                'ingestion_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Video ingestion completed: {ingestion_id}")
            return result
            
        except Exception as e:
            logger.error(f"Video ingestion failed for {ingestion_id}: {str(e)}")
            return {
                'success': False,
                'ingestion_id': ingestion_id,
                'error': f"Ingestion failed: {str(e)}",
                'step': 'unknown',
                'user_id': user_id
            }
    
    async def validate_url(self, url: str) -> Dict[str, Any]:
        """Validate video URL for ingestion."""
        try:
            # Basic URL format validation
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    'is_valid': False,
                    'error': 'Invalid URL format',
                    'url': url
                }
            
            # Platform support validation
            platform = self.get_platform_from_url(url)
            if platform == 'unsupported':
                return {
                    'is_valid': False,
                    'error': f'Unsupported platform: {parsed.netloc}',
                    'url': url
                }
            
            # yt-dlp validation
            is_valid, error_msg = await self.downloader.validate_url(url)
            if not is_valid:
                return {
                    'is_valid': False,
                    'error': error_msg or 'URL not supported by yt-dlp',
                    'url': url
                }
            
            return {
                'is_valid': True,
                'platform': platform,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"URL validation failed: {str(e)}")
            return {
                'is_valid': False,
                'error': f"Validation error: {str(e)}",
                'url': url
            }
    
    async def extract_metadata(self, url: str) -> Optional[VideoMetadata]:
        """Extract comprehensive metadata from video URL."""
        try:
            return await self.downloader.extract_metadata(url)
        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            return None
    
    async def validate_content(self, metadata: Optional[VideoMetadata], options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate video content against ingestion criteria."""
        if not metadata:
            return {
                'is_valid': False,
                'error': 'No metadata available for validation'
            }
        
        try:
            platform = metadata.platform
            platform_config = self.supported_platforms.get(platform, {})
            
            # Duration validation
            if metadata.duration:
                max_duration = platform_config.get('max_duration', 1800)  # Default 30 min
                if metadata.duration > max_duration:
                    return {
                        'is_valid': False,
                        'error': f'Video too long: {metadata.duration}s (max: {max_duration}s)'
                    }
            
            return {
                'is_valid': True,
                'platform': platform,
                'duration': metadata.duration
            }
            
        except Exception as e:
            logger.error(f"Content validation failed: {str(e)}")
            return {
                'is_valid': False,
                'error': f"Validation error: {str(e)}"
            }
    
    async def download_video(self, url: str, user_id: str, options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Download video with user-specific options."""
        try:
            # Build download options
            download_options = {
                'outtmpl': str(self.temp_dir / f'{user_id}_%(epoch)s_%(title)s.%(ext)s')
            }
            
            if options:
                # Quality preferences
                if 'quality' in options:
                    quality_map = {
                        'low': 'worst[height<=480]',
                        'medium': 'best[height<=720]',
                        'high': 'best[height<=1080]',
                        'best': 'best'
                    }
                    download_options['format'] = quality_map.get(options['quality'], 'best[height<=1080]')
            
            # Perform download
            result = await self.downloader.download_video(url, download_options)
            
            # Verify download
            file_path = result.get('filepath')
            if not file_path or not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': 'Download completed but file not found',
                    'result': result
                }
            
            return {
                'success': True,
                'file_path': file_path,
                'download_result': result,
                'download_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Video download failed: {str(e)}")
            return {
                'success': False,
                'error': f"Download failed: {str(e)}"
            }
    
    async def process_and_store(self, temp_file_path: str, metadata: Optional[VideoMetadata], user_id: str, ingestion_id: str) -> Dict[str, Any]:
        """Process and store downloaded video in organized structure."""
        try:
            # Generate organized file path
            if metadata and metadata.title:
                safe_title = safe_filename(metadata.title, max_length=100)
            else:
                safe_title = "unknown_video"
            
            # Create user directory
            user_dir = self.storage_dir / user_id
            ensure_directory(user_dir)
            
            # Generate final filename
            file_extension = Path(temp_file_path).suffix
            final_filename = f"{ingestion_id}_{safe_title}{file_extension}"
            final_path = user_dir / final_filename
            
            # Move file to final location
            import shutil
            shutil.move(temp_file_path, str(final_path))
            
            # Get basic file info
            file_info = {
                'size': os.path.getsize(str(final_path)),
                'path': str(final_path),
                'filename': final_filename
            }
            
            return {
                'success': True,
                'video_path': str(final_path),
                'file_info': file_info,
                'storage_location': 'local',
                'user_directory': str(user_dir)
            }
            
        except Exception as e:
            logger.error(f"Video storage failed: {str(e)}")
            return {
                'success': False,
                'error': f"Storage failed: {str(e)}"
            }
    
    async def download_thumbnail(self, url: str, ingestion_id: str) -> Optional[str]:
        """Download video thumbnail."""
        try:
            thumbnail_path = str(self.thumbnails_dir / f"{ingestion_id}_thumbnail.jpg")
            return await self.downloader.download_thumbnail(url, thumbnail_path)
        except Exception as e:
            logger.error(f"Thumbnail download failed: {str(e)}")
            return None
    
    def get_platform_from_url(self, url: str) -> str:
        """Determine platform from URL."""
        url_lower = url.lower()
        
        for platform, config in self.supported_platforms.items():
            for domain in config['domains']:
                if domain in url_lower:
                    return platform
        
        return 'unsupported'