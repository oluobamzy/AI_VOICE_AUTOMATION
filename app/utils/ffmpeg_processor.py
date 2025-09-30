"""
FFmpeg utilities for video processing.

This module provides comprehensive video processing capabilities
using FFmpeg with async support and error handling.
"""

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FFmpegProcessor:
    """
    Service for video processing using FFmpeg.
    
    Provides video conversion, encoding, subtitle overlay,
    and various video manipulation operations.
    """
    
    def __init__(self):
        self.ffmpeg_binary = settings.FFMPEG_BINARY
        self.ffprobe_binary = settings.FFPROBE_BINARY
        self.output_dir = Path(settings.PROCESSED_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify FFmpeg installation
        if not shutil.which(self.ffmpeg_binary):
            logger.warning(f"FFmpeg not found at {self.ffmpeg_binary}")
        if not shutil.which(self.ffprobe_binary):
            logger.warning(f"FFprobe not found at {self.ffprobe_binary}")
    
    async def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get comprehensive video information using ffprobe.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dict containing video metadata and technical information
        """
        logger.info(f"Getting video info for: {video_path}")
        
        cmd = [
            self.ffprobe_binary,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"FFprobe failed: {error_msg}")
            
            probe_data = json.loads(stdout.decode())
            
            # Extract video stream info
            video_stream = next(
                (s for s in probe_data['streams'] if s['codec_type'] == 'video'),
                None
            )
            
            # Extract audio stream info
            audio_stream = next(
                (s for s in probe_data['streams'] if s['codec_type'] == 'audio'),
                None
            )
            
            return {
                'format': probe_data['format'],
                'video_stream': video_stream,
                'audio_stream': audio_stream,
                'duration': float(probe_data['format'].get('duration', 0)),
                'size': int(probe_data['format'].get('size', 0)),
                'bitrate': int(probe_data['format'].get('bit_rate', 0)),
                'resolution': f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}" if video_stream else None,
                'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream else None,
                'codec': video_stream.get('codec_name') if video_stream else None,
                'audio_codec': audio_stream.get('codec_name') if audio_stream else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            raise
    
    async def convert_video(
        self,
        input_path: str,
        output_path: str,
        target_resolution: Optional[str] = None,
        target_format: str = "mp4",
        quality: str = "high",
        additional_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Convert video to specified format and resolution.
        
        Args:
            input_path: Input video file path
            output_path: Output video file path
            target_resolution: Target resolution (e.g., "1080x1920")
            target_format: Target format (mp4, mov, etc.)
            quality: Quality preset (low, medium, high, ultra)
            additional_args: Additional FFmpeg arguments
            
        Returns:
            Dict containing conversion results
        """
        logger.info(f"Converting video: {input_path} -> {output_path}")
        
        cmd = [self.ffmpeg_binary, "-i", input_path]
        
        # Quality settings
        quality_settings = {
            "low": ["-crf", "28", "-preset", "fast"],
            "medium": ["-crf", "23", "-preset", "medium"],
            "high": ["-crf", "20", "-preset", "slow"],
            "ultra": ["-crf", "18", "-preset", "veryslow"]
        }
        
        cmd.extend(quality_settings.get(quality, quality_settings["high"]))
        
        # Resolution scaling
        if target_resolution:
            cmd.extend(["-vf", f"scale={target_resolution}"])
        
        # Audio settings
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        
        # Additional arguments
        if additional_args:
            cmd.extend(additional_args)
        
        # Output settings
        cmd.extend(["-y", output_path])  # -y to overwrite output file
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"Video conversion failed: {error_msg}")
            
            # Get output file info
            output_info = await self.get_video_info(output_path)
            
            return {
                "success": True,
                "input_path": input_path,
                "output_path": output_path,
                "output_info": output_info,
                "conversion_log": stderr.decode() if stderr else ""
            }
            
        except Exception as e:
            logger.error(f"Video conversion failed: {str(e)}")
            raise
    
    async def add_subtitles(
        self,
        video_path: str,
        subtitle_text: str,
        output_path: str,
        font_size: int = 24,
        font_color: str = "white",
        background_color: str = "black@0.5",
        position: str = "center"
    ) -> Dict[str, Any]:
        """
        Add subtitles to video with custom styling.
        
        Args:
            video_path: Input video file path
            subtitle_text: Text to overlay as subtitles
            output_path: Output video file path
            font_size: Font size for subtitles
            font_color: Font color
            background_color: Background color with transparency
            position: Text position (center, bottom, top)
            
        Returns:
            Dict containing processing results
        """
        logger.info(f"Adding subtitles to video: {video_path}")
        
        # Position settings
        position_settings = {
            "center": "x=(w-text_w)/2:y=(h-text_h)/2",
            "bottom": "x=(w-text_w)/2:y=h-text_h-50",
            "top": "x=(w-text_w)/2:y=50"
        }
        
        pos = position_settings.get(position, position_settings["center"])
        
        # Create drawtext filter
        drawtext_filter = (
            f"drawtext=text='{subtitle_text}':fontsize={font_size}:"
            f"fontcolor={font_color}:box=1:boxcolor={background_color}:{pos}"
        )
        
        cmd = [
            self.ffmpeg_binary,
            "-i", video_path,
            "-vf", drawtext_filter,
            "-c:a", "copy",  # Copy audio without re-encoding
            "-y", output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"Subtitle addition failed: {error_msg}")
            
            return {
                "success": True,
                "input_path": video_path,
                "output_path": output_path,
                "subtitle_text": subtitle_text,
                "processing_log": stderr.decode() if stderr else ""
            }
            
        except Exception as e:
            logger.error(f"Subtitle addition failed: {str(e)}")
            raise
    
    async def extract_audio(
        self,
        video_path: str,
        output_path: str,
        format: str = "mp3",
        quality: str = "high"
    ) -> Dict[str, Any]:
        """
        Extract audio from video file.
        
        Args:
            video_path: Input video file path
            output_path: Output audio file path
            format: Audio format (mp3, wav, aac)
            quality: Audio quality
            
        Returns:
            Dict containing extraction results
        """
        logger.info(f"Extracting audio from: {video_path}")
        
        quality_settings = {
            "low": ["-b:a", "96k"],
            "medium": ["-b:a", "128k"],
            "high": ["-b:a", "192k"],
            "ultra": ["-b:a", "320k"]
        }
        
        cmd = [
            self.ffmpeg_binary,
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "mp3" if format == "mp3" else "pcm_s16le"
        ]
        
        cmd.extend(quality_settings.get(quality, quality_settings["high"]))
        cmd.extend(["-y", output_path])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"Audio extraction failed: {error_msg}")
            
            return {
                "success": True,
                "input_path": video_path,
                "output_path": output_path,
                "format": format,
                "quality": quality
            }
            
        except Exception as e:
            logger.error(f"Audio extraction failed: {str(e)}")
            raise
    
    async def create_thumbnail(
        self,
        video_path: str,
        output_path: str,
        timestamp: str = "00:00:01",
        size: str = "320x240"
    ) -> Dict[str, Any]:
        """
        Create thumbnail from video at specified timestamp.
        
        Args:
            video_path: Input video file path
            output_path: Output thumbnail file path
            timestamp: Timestamp for thumbnail (HH:MM:SS)
            size: Thumbnail size
            
        Returns:
            Dict containing thumbnail creation results
        """
        logger.info(f"Creating thumbnail for: {video_path}")
        
        cmd = [
            self.ffmpeg_binary,
            "-i", video_path,
            "-ss", timestamp,
            "-vframes", "1",
            "-s", size,
            "-y", output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"Thumbnail creation failed: {error_msg}")
            
            return {
                "success": True,
                "input_path": video_path,
                "output_path": output_path,
                "timestamp": timestamp,
                "size": size
            }
            
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {str(e)}")
            raise