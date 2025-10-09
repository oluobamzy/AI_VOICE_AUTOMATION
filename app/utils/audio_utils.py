"""
Audio processing utilities.

This module provides utilities for audio extraction, processing,
and optimization for transcription services.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import tempfile
import os

import ffmpeg

from app.core.logging import get_logger
from app.core.exceptions import AudioProcessingError
from app.utils.file_utils import ensure_directory_exists, get_file_extension

logger = get_logger(__name__)


class AudioProcessor:
    """
    Audio processing utility for video-to-audio extraction and optimization.
    """
    
    def __init__(self):
        """Initialize the audio processor."""
        self.supported_video_formats = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v'}
        self.supported_audio_formats = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'}
        self.temp_dir = Path(tempfile.gettempdir()) / "audio_processing"
        ensure_directory_exists(str(self.temp_dir))
    
    async def extract_audio_from_video(
        self,
        video_path: str,
        output_format: str = "wav",
        sample_rate: int = 16000
    ) -> str:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to video file
            output_format: Output audio format (wav, mp3, m4a)
            sample_rate: Target sample rate (16kHz optimal for Whisper)
            
        Returns:
            Path to extracted audio file
        """
        try:
            video_path = Path(video_path)
            if not video_path.exists():
                raise AudioProcessingError(f"Video file not found: {video_path}")
            
            # Create output path
            output_path = self.temp_dir / f"{video_path.stem}_audio.{output_format}"
            
            logger.info(f"Extracting audio from {video_path} to {output_path}")
            
            # Use ffmpeg to extract audio
            stream = ffmpeg.input(str(video_path))
            audio = stream.audio
            
            # Configure audio parameters for optimal transcription
            audio = audio.filter('aresample', sample_rate)
            
            if output_format == "wav":
                audio = audio.output(
                    str(output_path),
                    acodec='pcm_s16le',  # 16-bit PCM
                    ac=1,  # Mono channel
                    ar=sample_rate
                )
            elif output_format == "mp3":
                audio = audio.output(
                    str(output_path),
                    acodec='mp3',
                    ac=1,
                    ar=sample_rate,
                    audio_bitrate='128k'
                )
            else:
                audio = audio.output(str(output_path), ac=1, ar=sample_rate)
            
            # Run extraction
            await self._run_ffmpeg_async(audio)
            
            logger.info(f"Audio extracted successfully: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise AudioProcessingError(f"Failed to extract audio: {e}")
    
    async def optimize_for_transcription(
        self,
        audio_path: str,
        target_format: str = "wav",
        sample_rate: int = 16000,
        remove_noise: bool = True
    ) -> str:
        """
        Optimize audio file for transcription.
        
        Args:
            audio_path: Path to audio file
            target_format: Target format (wav recommended)
            sample_rate: Target sample rate
            remove_noise: Apply noise reduction
            
        Returns:
            Path to optimized audio file
        """
        try:
            audio_path = Path(audio_path)
            if not audio_path.exists():
                raise AudioProcessingError(f"Audio file not found: {audio_path}")
            
            output_path = self.temp_dir / f"{audio_path.stem}_optimized.{target_format}"
            
            logger.info(f"Optimizing audio {audio_path} for transcription")
            
            # Start with input
            stream = ffmpeg.input(str(audio_path))
            
            # Convert to mono
            audio = stream.audio.filter('pan', 'mono|c0=0.5*c0+0.5*c1')
            
            # Resample to target rate
            audio = audio.filter('aresample', sample_rate)
            
            # Apply high-pass filter to remove low-frequency noise
            audio = audio.filter('highpass', f=80)
            
            # Apply low-pass filter to remove high-frequency noise
            audio = audio.filter('lowpass', f=8000)
            
            # Normalize audio
            audio = audio.filter('loudnorm')
            
            # Optional noise reduction (basic implementation)
            if remove_noise:
                # Apply a gentle noise gate
                audio = audio.filter('gate', threshold=0.01, ratio=2, attack=5, release=50)
            
            # Output configuration
            audio = audio.output(
                str(output_path),
                acodec='pcm_s16le' if target_format == 'wav' else 'mp3',
                ac=1,  # Mono
                ar=sample_rate
            )
            
            await self._run_ffmpeg_async(audio)
            
            logger.info(f"Audio optimized: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Audio optimization failed: {e}")
            raise AudioProcessingError(f"Failed to optimize audio: {e}")
    
    async def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        Get detailed information about audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with audio metadata
        """
        try:
            audio_path = Path(audio_path)
            if not audio_path.exists():
                raise AudioProcessingError(f"Audio file not found: {audio_path}")
            
            # Use ffprobe to get audio information
            probe = ffmpeg.probe(str(audio_path))
            
            audio_stream = None
            for stream in probe['streams']:
                if stream['codec_type'] == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise AudioProcessingError("No audio stream found in file")
            
            # Extract relevant information
            info = {
                "duration": float(audio_stream.get('duration', 0)),
                "sample_rate": int(audio_stream.get('sample_rate', 0)),
                "channels": int(audio_stream.get('channels', 0)),
                "codec": audio_stream.get('codec_name', ''),
                "bitrate": int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else None,
                "format": probe.get('format', {}).get('format_name', ''),
                "file_size": int(probe.get('format', {}).get('size', 0))
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            raise AudioProcessingError(f"Failed to get audio info: {e}")
    
    async def split_audio_by_duration(
        self,
        audio_path: str,
        max_duration: int = 600,  # 10 minutes
        overlap: int = 30  # 30 seconds overlap
    ) -> List[str]:
        """
        Split long audio files into smaller chunks for processing.
        
        Args:
            audio_path: Path to audio file
            max_duration: Maximum duration per chunk (seconds)
            overlap: Overlap between chunks (seconds)
            
        Returns:
            List of paths to audio chunks
        """
        try:
            audio_info = await self.get_audio_info(audio_path)
            total_duration = audio_info['duration']
            
            if total_duration <= max_duration:
                return [audio_path]
            
            chunks = []
            audio_path = Path(audio_path)
            
            start_time = 0
            chunk_index = 0
            
            while start_time < total_duration:
                end_time = min(start_time + max_duration, total_duration)
                
                chunk_path = self.temp_dir / f"{audio_path.stem}_chunk_{chunk_index:03d}.wav"
                
                # Extract chunk
                stream = ffmpeg.input(str(audio_path), ss=start_time, t=end_time - start_time)
                audio = stream.audio.output(str(chunk_path), acodec='pcm_s16le')
                
                await self._run_ffmpeg_async(audio)
                chunks.append(str(chunk_path))
                
                # Move start time with overlap consideration
                start_time = end_time - overlap
                chunk_index += 1
            
            logger.info(f"Split audio into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Audio splitting failed: {e}")
            raise AudioProcessingError(f"Failed to split audio: {e}")
    
    async def merge_transcription_chunks(
        self,
        chunk_transcriptions: List[Dict[str, Any]],
        overlap_duration: int = 30
    ) -> Dict[str, Any]:
        """
        Merge transcriptions from audio chunks, handling overlaps.
        
        Args:
            chunk_transcriptions: List of transcription results
            overlap_duration: Overlap duration between chunks
            
        Returns:
            Merged transcription result
        """
        try:
            if not chunk_transcriptions:
                return {"text": "", "segments": [], "duration": 0}
            
            if len(chunk_transcriptions) == 1:
                return chunk_transcriptions[0]
            
            merged_text = ""
            merged_segments = []
            total_duration = 0
            time_offset = 0
            
            for i, chunk in enumerate(chunk_transcriptions):
                chunk_text = chunk.get("text", "")
                chunk_segments = chunk.get("segments", [])
                
                if i == 0:
                    # First chunk - include everything
                    merged_text += chunk_text
                    for segment in chunk_segments:
                        segment_copy = segment.copy()
                        segment_copy["start"] += time_offset
                        segment_copy["end"] += time_offset
                        merged_segments.append(segment_copy)
                else:
                    # Subsequent chunks - skip overlap
                    overlap_text = self._extract_overlap_text(chunk_text, overlap_duration)
                    remaining_text = chunk_text[len(overlap_text):]
                    merged_text += " " + remaining_text
                    
                    for segment in chunk_segments:
                        if segment.get("start", 0) >= overlap_duration:
                            segment_copy = segment.copy()
                            segment_copy["start"] = segment_copy["start"] - overlap_duration + time_offset
                            segment_copy["end"] = segment_copy["end"] - overlap_duration + time_offset
                            merged_segments.append(segment_copy)
                
                chunk_duration = chunk.get("duration", 0)
                if i < len(chunk_transcriptions) - 1:
                    time_offset += chunk_duration - overlap_duration
                else:
                    time_offset += chunk_duration
                total_duration = time_offset
            
            return {
                "text": merged_text.strip(),
                "segments": merged_segments,
                "duration": total_duration,
                "word_count": len(merged_text.split()),
                "confidence": self._calculate_merged_confidence(chunk_transcriptions)
            }
            
        except Exception as e:
            logger.error(f"Chunk merging failed: {e}")
            raise AudioProcessingError(f"Failed to merge chunks: {e}")
    
    async def _run_ffmpeg_async(self, stream) -> None:
        """Run ffmpeg command asynchronously."""
        try:
            # Create a new event loop for the subprocess
            loop = asyncio.get_event_loop()
            
            # Run ffmpeg in a separate thread to avoid blocking
            def run_ffmpeg():
                try:
                    stream.run(overwrite_output=True, quiet=True)
                except ffmpeg.Error as e:
                    logger.error(f"FFmpeg error: {e}")
                    raise AudioProcessingError(f"FFmpeg error: {e}")
            
            await loop.run_in_executor(None, run_ffmpeg)
            
        except Exception as e:
            logger.error(f"FFmpeg execution failed: {e}")
            raise AudioProcessingError(f"FFmpeg execution failed: {e}")
    
    def _extract_overlap_text(self, text: str, overlap_duration: int) -> str:
        """Extract text that corresponds to overlap duration (simplified)."""
        # This is a simplified implementation
        # In practice, you'd use timing information from segments
        words = text.split()
        # Rough estimate: ~2-3 words per second
        overlap_words = min(len(words), overlap_duration * 2)
        return " ".join(words[:overlap_words])
    
    def _calculate_merged_confidence(self, chunk_transcriptions: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence from chunk transcriptions."""
        confidences = [chunk.get("confidence", 0.9) for chunk in chunk_transcriptions]
        return sum(confidences) / len(confidences) if confidences else 0.9
    
    def cleanup_temp_files(self, keep_recent: int = 5) -> None:
        """
        Clean up temporary audio files.
        
        Args:
            keep_recent: Number of recent files to keep
        """
        try:
            if not self.temp_dir.exists():
                return
            
            files = list(self.temp_dir.glob("*"))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old files beyond keep_recent limit
            for file_path in files[keep_recent:]:
                try:
                    file_path.unlink()
                    logger.debug(f"Cleaned up temp file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")