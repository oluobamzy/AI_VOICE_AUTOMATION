"""
Video downloader service.

This module provides advanced video downloading capabilities using yt-dlp
with support for multiple platforms, metadata extraction, and error handling.
"""

import asyncio
import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse

import yt_dlp
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.video import VideoMetadata, VideoCreate
from app.utils.file_utils import ensure_directory, get_file_size, get_file_hash

logger = get_logger(__name__)


class VideoDownloader:
    """
    Advanced service for downloading videos from various platforms.
    
    Supports TikTok, YouTube, Instagram, Twitter, and other platforms
    via yt-dlp integration with platform-specific optimizations.
    """
    
    # Platform-specific configurations
    PLATFORM_CONFIGS = {
        'tiktok': {
            'format': 'best[height<=1080]/best',
            'writesubtitles': False,  # TikTok rarely has subtitles
            'writeautomaticsub': False,
            'extract_flat': False,
        },
        'youtube': {
            'format': 'best[height<=1080]/best',
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en', 'en-US'],
            'extract_flat': False,
        },
        'instagram': {
            'format': 'best[height<=1080]/best',
            'writesubtitles': False,
            'writeautomaticsub': False,
        },
        'twitter': {
            'format': 'best[height<=1080]/best',
            'writesubtitles': False,
            'writeautomaticsub': False,
        }
    }
    
    def __init__(self):
        self.download_dir = Path(settings.UPLOAD_DIR) / "downloads"
        self.temp_dir = Path(settings.UPLOAD_DIR) / "temp"
        
        # Ensure directories exist
        ensure_directory(self.download_dir)
        ensure_directory(self.temp_dir)
        
        # Base yt-dlp options
        self.base_options = {
            'format': 'best[height<=1080]/best',
            'outtmpl': str(self.download_dir / '%(epoch)s_%(title)s.%(ext)s'),
            'writeinfojson': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'ignoreerrors': False,
            'no_warnings': False,
            'extractflat': False,
            'cookiefile': None,
            'age_limit': None,
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 60,
            'geo_bypass': True,
            'nocheckcertificate': True,
        }
    
    def get_platform_from_url(self, url: str) -> str:
        """
        Determine platform from URL.
        
        Args:
            url: Video URL
            
        Returns:
            Platform name (tiktok, youtube, instagram, twitter, etc.)
        """
        url_lower = url.lower()
        
        if 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
            return 'facebook'
        else:
            return 'generic'
    
    def build_download_options(self, url: str, custom_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build yt-dlp options based on platform and custom options.
        
        Args:
            url: Video URL
            custom_options: Custom options to override defaults
            
        Returns:
            Complete yt-dlp options dict
        """
        platform = self.get_platform_from_url(url)
        
        # Start with base options
        options = self.base_options.copy()
        
        # Apply platform-specific options
        if platform in self.PLATFORM_CONFIGS:
            platform_config = self.PLATFORM_CONFIGS[platform]
            options.update(platform_config)
        
        # Apply custom options
        if custom_options:
            options.update(custom_options)
        
        # Ensure unique output filename
        timestamp = int(datetime.now().timestamp())
        if 'outtmpl' not in (custom_options or {}):
            options['outtmpl'] = str(self.download_dir / f'{timestamp}_%(title)s.%(ext)s')
        
        return options
    
    async def download_video(
        self, 
        url: str, 
        options: Optional[Dict[str, Any]] = None,
        extract_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Download a video from the given URL with enhanced error handling.
        
        Args:
            url: The video URL to download
            options: Additional yt-dlp options
            extract_metadata: Whether to extract detailed metadata
            
        Returns:
            Dict containing download results and metadata
            
        Raises:
            DownloadError: If download fails
            ExtractorError: If URL extraction fails
        """
        logger.info(f"Starting video download from: {url}")
        platform = self.get_platform_from_url(url)
        logger.info(f"Detected platform: {platform}")
        
        # Build download options
        ydl_opts = self.build_download_options(url, options)
        
        try:
            # Run yt-dlp in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._download_with_ytdl, 
                url, 
                ydl_opts,
                extract_metadata
            )
            
            # Enhance result with additional metadata
            result['platform'] = platform
            result['download_timestamp'] = datetime.now().isoformat()
            result['download_options'] = ydl_opts
            
            # Calculate file hash and size if file exists
            if result.get('filepath') and os.path.exists(result['filepath']):
                result['file_size'] = get_file_size(result['filepath'])
                result['file_hash'] = await get_file_hash(result['filepath'])
            
            logger.info(f"Video download completed: {result.get('title', 'Unknown')}")
            return result
            
        except (DownloadError, ExtractorError) as e:
            logger.error(f"yt-dlp error during download: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during video download: {str(e)}")
            raise DownloadError(f"Download failed: {str(e)}")
    
    def _download_with_ytdl(self, url: str, options: Dict[str, Any], extract_metadata: bool = True) -> Dict[str, Any]:
        """
        Synchronous wrapper for yt-dlp download with enhanced metadata extraction.
        
        Args:
            url: Video URL
            options: yt-dlp options
            extract_metadata: Whether to extract detailed metadata
            
        Returns:
            Dict with download results and metadata
        """
        with YoutubeDL(options) as ydl:
            try:
                # Extract info without downloading first
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise ExtractorError("Failed to extract video information")
                
                # Prepare filename and check if it already exists
                filename = ydl.prepare_filename(info)
                
                # Download the video
                ydl.download([url])
                
                # Build comprehensive result
                result = {
                    'title': info.get('title'),
                    'description': info.get('description'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'uploader_id': info.get('uploader_id'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'comment_count': info.get('comment_count'),
                    'tags': info.get('tags', []),
                    'categories': info.get('categories', []),
                    'thumbnail': info.get('thumbnail'),
                    'thumbnails': info.get('thumbnails', []),
                    'webpage_url': info.get('webpage_url'),
                    'original_url': url,
                    'extractor': info.get('extractor'),
                    'extractor_key': info.get('extractor_key'),
                    'filepath': filename,
                    'filename': os.path.basename(filename),
                    'format_id': info.get('format_id'),
                    'format_note': info.get('format_note'),
                    'resolution': f"{info.get('width', 0)}x{info.get('height', 0)}",
                    'width': info.get('width'),
                    'height': info.get('height'),
                    'fps': info.get('fps'),
                    'filesize': info.get('filesize'),
                    'filesize_approx': info.get('filesize_approx'),
                    'vcodec': info.get('vcodec'),
                    'acodec': info.get('acodec'),
                    'abr': info.get('abr'),  # Audio bitrate
                    'vbr': info.get('vbr'),  # Video bitrate
                    'container': info.get('container'),
                    'protocol': info.get('protocol'),
                    'language': info.get('language'),
                    'age_limit': info.get('age_limit'),
                    'is_live': info.get('is_live', False),
                    'was_live': info.get('was_live', False),
                }
                
                # Extract platform-specific metadata
                if extract_metadata:
                    result.update(self._extract_platform_metadata(info))
                
                return result
                
            except DownloadError as e:
                logger.error(f"yt-dlp download error: {str(e)}")
                raise
            except ExtractorError as e:
                logger.error(f"yt-dlp extractor error: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in yt-dlp: {str(e)}")
                raise DownloadError(f"Download failed: {str(e)}")
    
    def _extract_platform_metadata(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract platform-specific metadata.
        
        Args:
            info: yt-dlp info dict
            
        Returns:
            Dict with platform-specific metadata
        """
        metadata = {}
        extractor = info.get('extractor_key', '').lower()
        
        if extractor == 'tiktok':
            metadata.update({
                'tiktok_id': info.get('id'),
                'tiktok_user': info.get('uploader_id'),
                'tiktok_music': info.get('track'),
                'tiktok_effects': info.get('effects', []),
                'tiktok_hashtags': self._extract_hashtags_from_description(info.get('description', '')),
            })
        elif extractor in ['youtube', 'youtubetab']:
            metadata.update({
                'youtube_id': info.get('id'),
                'youtube_channel': info.get('channel'),
                'youtube_channel_id': info.get('channel_id'),
                'youtube_channel_url': info.get('channel_url'),
                'youtube_playlist': info.get('playlist'),
                'youtube_playlist_index': info.get('playlist_index'),
                'youtube_live_status': info.get('live_status'),
                'youtube_availability': info.get('availability'),
            })
        elif extractor == 'instagram':
            metadata.update({
                'instagram_id': info.get('id'),
                'instagram_user': info.get('uploader_id'),
                'instagram_shortcode': info.get('display_id'),
                'instagram_media_type': 'video',
            })
        elif extractor == 'twitter':
            metadata.update({
                'twitter_id': info.get('id'),
                'twitter_user': info.get('uploader_id'),
                'twitter_user_id': info.get('uploader_id'),
                'twitter_retweet_count': info.get('repost_count'),
            })
        
        return metadata
    
    def _extract_hashtags_from_description(self, description: str) -> List[str]:
        """Extract hashtags from description text."""
        if not description:
            return []
        
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, description)
        return [tag.lstrip('#') for tag in hashtags]

    async def extract_metadata(self, url: str) -> VideoMetadata:
        """
        Extract comprehensive metadata from a video URL without downloading.
        
        Args:
            url: The video URL
            
        Returns:
            VideoMetadata: Extracted metadata
        """
        logger.info(f"Extracting metadata from: {url}")
        platform = self.get_platform_from_url(url)
        
        options = self.build_download_options(url)
        options['skip_download'] = True
        
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._extract_info_only,
                url,
                options
            )
            
            # Build VideoMetadata object
            metadata = VideoMetadata(
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
                hashtags=info.get('tags', []),
                upload_date=info.get('upload_date'),
                platform=platform,
                original_url=url,
                extractor=info.get('extractor')
            )
            
            logger.info(f"Metadata extraction completed for: {metadata.title}")
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            raise ExtractorError(f"Failed to extract metadata: {str(e)}")
    
    def _extract_info_only(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract info without downloading."""
        with YoutubeDL(options) as ydl:
            return ydl.extract_info(url, download=False)
    
    async def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a URL is supported for download.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            options = {'quiet': True, 'skip_download': True}
            loop = asyncio.get_event_loop()
            
            await loop.run_in_executor(
                None,
                self._extract_info_only,
                url,
                options
            )
            return True, None
            
        except Exception as e:
            error_msg = f"URL validation failed: {str(e)}"
            logger.warning(error_msg)
            return False, error_msg
    
    async def get_supported_sites(self) -> List[str]:
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
            return sorted([
                extractor.IE_NAME for extractor in sites 
                if hasattr(extractor, 'IE_NAME') and extractor.IE_NAME
            ])
        except Exception as e:
            logger.error(f"Failed to get supported sites: {str(e)}")
            return []
    
    async def get_video_formats(self, url: str) -> List[Dict[str, Any]]:
        """
        Get available video formats for a URL.
        
        Args:
            url: Video URL
            
        Returns:
            List of available formats
        """
        try:
            options = {'quiet': True, 'skip_download': True, 'listformats': True}
            loop = asyncio.get_event_loop()
            
            info = await loop.run_in_executor(
                None,
                self._extract_info_only,
                url,
                options
            )
            
            formats = info.get('formats', [])
            return [
                {
                    'format_id': fmt.get('format_id'),
                    'ext': fmt.get('ext'),
                    'resolution': f"{fmt.get('width', 0)}x{fmt.get('height', 0)}",
                    'fps': fmt.get('fps'),
                    'filesize': fmt.get('filesize'),
                    'vcodec': fmt.get('vcodec'),
                    'acodec': fmt.get('acodec'),
                    'quality': fmt.get('quality'),
                    'format_note': fmt.get('format_note')
                }
                for fmt in formats
                if fmt.get('vcodec') != 'none'  # Filter out audio-only formats
            ]
            
        except Exception as e:
            logger.error(f"Failed to get video formats: {str(e)}")
            return []
    
    async def download_thumbnail(self, url: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Download video thumbnail.
        
        Args:
            url: Video URL
            output_path: Optional output path for thumbnail
            
        Returns:
            Path to downloaded thumbnail or None if failed
        """
        try:
            if not output_path:
                timestamp = int(datetime.now().timestamp())
                output_path = str(self.download_dir / f'thumbnail_{timestamp}.jpg')
            
            options = {
                'skip_download': True,
                'writethumbnail': True,
                'outtmpl': output_path.replace('.jpg', ''),  # yt-dlp adds extension
                'quiet': True
            }
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._download_thumbnail_sync,
                url,
                options
            )
            
            # Check if thumbnail was downloaded
            possible_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            base_path = output_path.replace('.jpg', '')
            
            for ext in possible_extensions:
                thumb_path = base_path + ext
                if os.path.exists(thumb_path):
                    logger.info(f"Thumbnail downloaded: {thumb_path}")
                    return thumb_path
            
            return None
            
        except Exception as e:
            logger.error(f"Thumbnail download failed: {str(e)}")
            return None
    
    def _download_thumbnail_sync(self, url: str, options: Dict[str, Any]) -> None:
        """Synchronous thumbnail download."""
        with YoutubeDL(options) as ydl:
            ydl.download([url])
    
    async def clean_old_downloads(self, days_old: int = 7) -> Dict[str, Any]:
        """
        Clean up old downloaded files.
        
        Args:
            days_old: Delete files older than this many days
            
        Returns:
            Dict with cleanup results
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            cleaned_files = 0
            freed_space = 0
            
            for file_path in self.download_dir.glob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    cleaned_files += 1
                    freed_space += file_size
                    logger.info(f"Deleted old file: {file_path.name}")
            
            return {
                'success': True,
                'cleaned_files': cleaned_files,
                'freed_space_mb': freed_space / (1024 * 1024),
                'cutoff_days': days_old
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }