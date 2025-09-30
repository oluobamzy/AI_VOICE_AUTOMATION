"""
Video downloader service.

This module provides video downloading capabilities using yt-dlp
with support for multiple platforms and metadata extraction.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

import yt_dlp
from yt_dlp import YoutubeDL

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.video import VideoMetadata

logger = get_logger(__name__)


class VideoDownloader:
    """
    Service for downloading videos from various platforms.
    
    Supports TikTok, YouTube, Instagram, Twitter, and other platforms
    via yt-dlp integration.
    """
    
    def __init__(self):
        self.download_dir = Path(settings.UPLOAD_DIR)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Default yt-dlp options
        self.default_options = {
            'format': 'best[height<=1080]',
            'outtmpl': str(self.download_dir / '%(title)s.%(ext)s'),
            'writeinfojson': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'ignoreerrors': True,
            'no_warnings': False,
            'extractflat': False,
        }
    
    async def download_video(
        self, 
        url: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Download a video from the given URL.
        
        Args:
            url: The video URL to download
            options: Additional yt-dlp options
            
        Returns:
            Dict containing download results and metadata
            
        Raises:
            Exception: If download fails
        """
        logger.info(f"Starting video download from: {url}")
        
        # Merge custom options with defaults
        ydl_opts = self.default_options.copy()
        if options:
            ydl_opts.update(options)
        
        try:
            # Run yt-dlp in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._download_with_ytdl, 
                url, 
                ydl_opts
            )
            
            logger.info(f"Video download completed: {result.get('title', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Video download failed: {str(e)}")
            raise
    
    def _download_with_ytdl(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for yt-dlp download.
        
        Args:
            url: Video URL
            options: yt-dlp options
            
        Returns:
            Dict with download results
        """
        with YoutubeDL(options) as ydl:
            # Extract info without downloading first
            info = ydl.extract_info(url, download=False)
            
            # Download the video
            ydl.download([url])
            
            return {
                'title': info.get('title'),
                'description': info.get('description'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'upload_date': info.get('upload_date'),
                'view_count': info.get('view_count'),
                'like_count': info.get('like_count'),
                'comment_count': info.get('comment_count'),
                'tags': info.get('tags', []),
                'thumbnail': info.get('thumbnail'),
                'webpage_url': info.get('webpage_url'),
                'extractor': info.get('extractor'),
                'filename': ydl.prepare_filename(info),
                'format_id': info.get('format_id'),
                'resolution': f"{info.get('width', 0)}x{info.get('height', 0)}",
                'fps': info.get('fps'),
                'filesize': info.get('filesize'),
            }
    
    async def extract_metadata(self, url: str) -> VideoMetadata:
        """
        Extract metadata from a video URL without downloading.
        
        Args:
            url: The video URL
            
        Returns:
            VideoMetadata: Extracted metadata
        """
        logger.info(f"Extracting metadata from: {url}")
        
        options = self.default_options.copy()
        options['skip_download'] = True
        
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._extract_info_only,
                url,
                options
            )
            
            return VideoMetadata(
                title=info.get('title'),
                description=info.get('description'),
                duration=info.get('duration'),
                resolution=f"{info.get('width', 0)}x{info.get('height', 0)}",
                fps=info.get('fps'),
                codec=info.get('vcodec'),
                audio_codec=info.get('acodec'),
                thumbnail_url=info.get('thumbnail'),
                view_count=info.get('view_count'),
                like_count=info.get('like_count'),
                comment_count=info.get('comment_count'),
                uploader=info.get('uploader'),
                uploader_id=info.get('uploader_id'),
                hashtags=info.get('tags', [])
            )
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            raise
    
    def _extract_info_only(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract info without downloading."""
        with YoutubeDL(options) as ydl:
            return ydl.extract_info(url, download=False)
    
    async def get_supported_sites(self) -> list:
        """
        Get list of supported sites for video downloading.
        
        Returns:
            List of supported site names
        """
        try:
            loop = asyncio.get_event_loop()
            sites = await loop.run_in_executor(
                None,
                lambda: list(yt_dlp.extractor.gen_extractors())
            )
            return [extractor.IE_NAME for extractor in sites if hasattr(extractor, 'IE_NAME')]
        except Exception as e:
            logger.error(f"Failed to get supported sites: {str(e)}")
            return []
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if a URL is supported for download.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is supported
        """
        try:
            with YoutubeDL({'quiet': True}) as ydl:
                ydl.extract_info(url, download=False)
                return True
        except Exception:
            return False