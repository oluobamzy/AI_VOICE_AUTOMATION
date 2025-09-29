import openai
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.models.schemas import AvatarConfig
from app.utils.ffmpeg import ffmpeg_processor


class AvatarService:
    """Handle AI avatar generation and voice synthesis"""
    
    def __init__(self):
        self.temp_dir = Path(settings.temp_video_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
    
    async def generate_script(self, video_metadata: Dict[str, Any], custom_prompt: Optional[str] = None) -> str:
        """Generate script using AI based on video content"""
        try:
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            # Build prompt based on video metadata
            base_prompt = f"""
            Create an engaging script for a short-form video based on this content:
            - Duration: {video_metadata.get('duration', 'unknown')} seconds
            - Resolution: {video_metadata.get('resolution', 'unknown')}
            - Platform: {video_metadata.get('platform', 'unknown')}
            
            The script should be:
            - Engaging and attention-grabbing
            - Suitable for the target platform
            - Natural sounding for voice synthesis
            - Concise and impactful
            """
            
            if custom_prompt:
                base_prompt += f"\n\nAdditional requirements: {custom_prompt}"
            
            response = await openai.ChatCompletion.acreate(
                model=settings.avatar_model,
                messages=[
                    {"role": "system", "content": "You are a creative script writer for viral social media content."},
                    {"role": "user", "content": base_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            script = response.choices[0].message.content.strip()
            logger.info("AI script generated successfully")
            return script
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            raise
    
    async def synthesize_voice(
        self, 
        script: str, 
        avatar_config: AvatarConfig,
        output_path: str
    ) -> str:
        """Synthesize voice from script using AI voice models"""
        try:
            # This is a placeholder for actual voice synthesis
            # In production, you'd integrate with services like:
            # - ElevenLabs API
            # - Azure Cognitive Services
            # - Google Cloud Text-to-Speech
            # - Amazon Polly
            
            logger.info("Voice synthesis started")
            
            # Placeholder: create a silent audio file for now
            # In real implementation, this would call the voice synthesis API
            duration = len(script.split()) * 0.5  # Rough estimate: 0.5 seconds per word
            
            # Create silent audio file using FFmpeg (placeholder)
            import subprocess
            cmd = [
                "ffmpeg", "-f", "lavfi", "-i", f"anullsrc=duration={duration}:sample_rate=44100",
                "-c:a", "pcm_s16le", output_path, "-y"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info(f"Voice synthesis completed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error synthesizing voice: {e}")
            raise
    
    async def create_avatar_video(
        self,
        script: str,
        avatar_config: AvatarConfig,
        background_video_path: Optional[str] = None
    ) -> str:
        """Create avatar video with synthesized voice"""
        try:
            output_filename = f"avatar_video_{hash(script)}.mp4"
            output_path = str(self.temp_dir / output_filename)
            
            # Synthesize voice
            audio_filename = f"avatar_audio_{hash(script)}.wav"
            audio_path = str(self.temp_dir / audio_filename)
            await self.synthesize_voice(script, avatar_config, audio_path)
            
            if background_video_path:
                # Add synthesized audio to existing video
                final_output = await ffmpeg_processor.add_audio_to_video(
                    video_path=background_video_path,
                    audio_path=audio_path,
                    output_path=output_path
                )
            else:
                # Create video with static image/avatar and audio
                # This is a placeholder - in production you'd have actual avatar generation
                duration_cmd = ["ffprobe", "-v", "quiet", "-show_entries", 
                               "format=duration", "-of", "csv=p=0", audio_path]
                import subprocess
                result = subprocess.run(duration_cmd, capture_output=True, text=True)
                duration = float(result.stdout.strip())
                
                # Create video with solid color background (placeholder for avatar)
                cmd = [
                    "ffmpeg", "-f", "lavfi", 
                    "-i", f"color=c=blue:size=1080x1920:duration={duration}",
                    "-i", audio_path,
                    "-c:v", "libx264", "-c:a", "aac",
                    "-shortest", output_path, "-y"
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                final_output = output_path
            
            logger.info(f"Avatar video created: {final_output}")
            return final_output
            
        except Exception as e:
            logger.error(f"Error creating avatar video: {e}")
            raise


# Global instance
avatar_service = AvatarService()