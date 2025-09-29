import httpx
import os
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse
from app.core.config import settings
from app.core.logging import logger
from app.utils.ffmpeg import ffmpeg_processor


class VideoIngester:
    """Handle video ingestion from various platforms"""
    
    def __init__(self):
        self.temp_dir = Path(settings.temp_video_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    async def download_video(self, url: str, filename: str = None) -> str:
        """Download video from URL"""
        try:
            if not filename:
                parsed_url = urlparse(url)
                filename = f"video_{hash(url)}.mp4"
            
            output_path = self.temp_dir / filename
            
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    
                    with open(output_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
            
            logger.info(f"Downloaded video: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error downloading video from {url}: {e}")
            raise
    
    async def validate_video(self, video_path: str) -> Dict[str, Any]:
        """Validate downloaded video"""
        try:
            # Check file exists and has content
            if not os.path.exists(video_path):
                raise ValueError(f"Video file not found: {video_path}")
            
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                raise ValueError("Downloaded video file is empty")
            
            # Get video metadata
            video_info = await ffmpeg_processor.get_video_info(video_path)
            
            # Validate video constraints
            max_size_bytes = settings.max_video_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                raise ValueError(f"Video too large: {file_size} bytes (max: {max_size_bytes})")
            
            return {
                "valid": True,
                "file_size": file_size,
                "video_info": video_info
            }
            
        except Exception as e:
            logger.error(f"Video validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def extract_metadata(self, video_path: str, source_url: str) -> Dict[str, Any]:
        """Extract metadata from video and source"""
        try:
            video_info = await ffmpeg_processor.get_video_info(video_path)
            
            metadata = {
                "source_url": source_url,
                "file_path": video_path,
                "file_size": os.path.getsize(video_path),
                "duration": video_info["duration"],
                "resolution": f"{video_info['width']}x{video_info['height']}",
                "fps": video_info["fps"],
                "codec": video_info["codec"],
                "bitrate": video_info.get("bitrate", 0)
            }
            
            # Platform-specific metadata extraction could go here
            # e.g., TikTok API, YouTube API calls
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            raise


# Global instance
video_ingester = VideoIngester()