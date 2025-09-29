from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.utils.ffmpeg import ffmpeg_processor


class VideoTransformer:
    """Handle video transformation operations"""
    
    def __init__(self):
        self.temp_dir = Path(settings.temp_video_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    async def transform_for_platform(
        self, 
        input_path: str, 
        platform: str,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Transform video for specific platform requirements"""
        try:
            output_filename = f"transformed_{platform}_{Path(input_path).stem}.mp4"
            output_path = str(self.temp_dir / output_filename)
            
            # Platform-specific configurations
            platform_configs = {
                "youtube": {
                    "resolution": (1920, 1080),
                    "target_size_mb": 128,
                    "format": "mp4"
                },
                "tiktok": {
                    "resolution": (1080, 1920),  # Vertical
                    "target_size_mb": 32,
                    "format": "mp4"
                },
                "instagram": {
                    "resolution": (1080, 1920),  # Vertical  
                    "target_size_mb": 64,
                    "format": "mp4"
                }
            }
            
            config = platform_configs.get(platform.lower(), platform_configs["youtube"])
            if custom_config:
                config.update(custom_config)
            
            # Compress and resize video
            await ffmpeg_processor.compress_video(
                input_path=input_path,
                output_path=output_path,
                target_size_mb=config.get("target_size_mb"),
                target_resolution=config.get("resolution")
            )
            
            logger.info(f"Video transformed for {platform}: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error transforming video for {platform}: {e}")
            raise
    
    async def apply_filters(
        self, 
        input_path: str, 
        filters: Dict[str, Any]
    ) -> str:
        """Apply custom filters to video"""
        try:
            output_filename = f"filtered_{Path(input_path).stem}.mp4"
            output_path = str(self.temp_dir / output_filename)
            
            # This is a simplified implementation
            # In production, you'd implement specific filter logic
            logger.info(f"Applying filters: {filters}")
            
            # For now, just copy the file (placeholder for actual filter implementation)
            import shutil
            shutil.copy2(input_path, output_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            raise
    
    async def optimize_for_streaming(self, input_path: str) -> str:
        """Optimize video for streaming"""
        try:
            output_filename = f"optimized_{Path(input_path).stem}.mp4"
            output_path = str(self.temp_dir / output_filename)
            
            # Optimize for streaming (fast start, proper encoding)
            await ffmpeg_processor.compress_video(
                input_path=input_path,
                output_path=output_path,
                target_resolution=(1920, 1080)
            )
            
            logger.info(f"Video optimized for streaming: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error optimizing video for streaming: {e}")
            raise


# Global instance
video_transformer = VideoTransformer()