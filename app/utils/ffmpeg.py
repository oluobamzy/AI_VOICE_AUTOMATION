import ffmpeg
import os
from typing import Dict, Any, Optional
from pathlib import Path
from app.core.config import settings
from app.core.logging import logger


class FFmpegProcessor:
    """FFmpeg video processing utilities"""
    
    def __init__(self):
        self.ffmpeg_path = settings.ffmpeg_path
        self.temp_dir = Path(settings.temp_video_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    async def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using ffprobe"""
        try:
            probe = ffmpeg.probe(video_path)
            video_info = next(
                stream for stream in probe["streams"] 
                if stream["codec_type"] == "video"
            )
            
            return {
                "duration": float(probe["format"]["duration"]),
                "width": int(video_info["width"]),
                "height": int(video_info["height"]),
                "fps": eval(video_info["r_frame_rate"]),
                "codec": video_info["codec_name"],
                "bitrate": int(probe["format"].get("bit_rate", 0)),
                "size": int(probe["format"]["size"])
            }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise
    
    async def compress_video(
        self, 
        input_path: str, 
        output_path: str,
        target_size_mb: Optional[int] = None,
        target_resolution: Optional[tuple] = None
    ) -> str:
        """Compress video for different platforms"""
        try:
            stream = ffmpeg.input(input_path)
            
            # Set target resolution (default to 1080x1920 for shorts)
            if target_resolution:
                stream = ffmpeg.filter(stream, "scale", target_resolution[0], target_resolution[1])
            else:
                stream = ffmpeg.filter(stream, "scale", 1080, 1920)
            
            # Calculate bitrate if target size is specified
            if target_size_mb:
                video_info = await self.get_video_info(input_path)
                duration = video_info["duration"]
                target_bitrate = int((target_size_mb * 8 * 1024 * 1024) / duration * 0.9)  # 90% for video
                
                stream = ffmpeg.output(
                    stream,
                    output_path,
                    vcodec="libx264",
                    acodec="aac",
                    video_bitrate=f"{target_bitrate}k",
                    audio_bitrate="128k",
                    preset="medium"
                )
            else:
                stream = ffmpeg.output(
                    stream,
                    output_path,
                    vcodec="libx264",
                    acodec="aac",
                    crf=23,
                    preset="medium"
                )
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return output_path
            
        except Exception as e:
            logger.error(f"Error compressing video: {e}")
            raise
    
    async def extract_audio(self, video_path: str, output_path: str) -> str:
        """Extract audio from video"""
        try:
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, output_path, acodec="pcm_s16le")
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return output_path
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
    
    async def add_audio_to_video(
        self, 
        video_path: str, 
        audio_path: str, 
        output_path: str
    ) -> str:
        """Add audio track to video"""
        try:
            video = ffmpeg.input(video_path)
            audio = ffmpeg.input(audio_path)
            
            out = ffmpeg.output(
                video, audio,
                output_path,
                vcodec="copy",
                acodec="aac",
                shortest=None
            )
            
            ffmpeg.run(out, overwrite_output=True, quiet=True)
            return output_path
        except Exception as e:
            logger.error(f"Error adding audio to video: {e}")
            raise
    
    async def create_thumbnail(self, video_path: str, output_path: str, time: float = 1.0) -> str:
        """Create thumbnail from video at specified time"""
        try:
            stream = ffmpeg.input(video_path, ss=time)
            stream = ffmpeg.output(stream, output_path, vframes=1, format="image2")
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return output_path
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            raise


# Global instance
ffmpeg_processor = FFmpegProcessor()