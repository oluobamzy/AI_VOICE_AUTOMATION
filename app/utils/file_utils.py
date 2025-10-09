"""
File utility functions.

This module provides utility functions for file operations,
directory management, and file metadata extraction.
"""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import aiofiles
import asyncio

from app.core.logging import get_logger

logger = get_logger(__name__)


def ensure_directory(path: Path) -> None:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        path: Directory path to ensure
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {path}")
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes
    """
    try:
        return os.path.getsize(file_path)
    except OSError as e:
        logger.error(f"Failed to get file size for {file_path}: {e}")
        return 0


async def get_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate file hash asynchronously.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm to use
        
    Returns:
        File hash as hex string
    """
    try:
        hash_obj = hashlib.new(algorithm)
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
        
    except Exception as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        return ""


def get_file_extension(file_path: str) -> str:
    """
    Get file extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        File extension (without dot)
    """
    return Path(file_path).suffix.lstrip('.')


def get_filename_without_extension(file_path: str) -> str:
    """
    Get filename without extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        Filename without extension
    """
    return Path(file_path).stem


def safe_filename(filename: str, max_length: int = 200) -> str:
    """
    Create a safe filename by removing/replacing problematic characters.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Safe filename
    """
    # Replace problematic characters
    import re
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    safe_name = safe_name.strip(' .')
    
    # Limit length
    if len(safe_name) > max_length:
        name, ext = os.path.splitext(safe_name)
        max_name_length = max_length - len(ext)
        safe_name = name[:max_name_length] + ext
    
    return safe_name


def move_file(source: str, destination: str) -> bool:
    """
    Move file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure destination directory exists
        ensure_directory(Path(destination).parent)
        
        shutil.move(source, destination)
        logger.info(f"File moved: {source} -> {destination}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to move file {source} to {destination}: {e}")
        return False


def copy_file(source: str, destination: str) -> bool:
    """
    Copy file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure destination directory exists
        ensure_directory(Path(destination).parent)
        
        shutil.copy2(source, destination)
        logger.info(f"File copied: {source} -> {destination}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to copy file {source} to {destination}: {e}")
        return False


def delete_file(file_path: str) -> bool:
    """
    Delete a file.
    
    Args:
        file_path: Path to file to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.remove(file_path)
        logger.info(f"File deleted: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete file {file_path}: {e}")
        return False


def get_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Get comprehensive file metadata.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dict containing file metadata
    """
    try:
        stat = os.stat(file_path)
        path_obj = Path(file_path)
        
        return {
            'name': path_obj.name,
            'stem': path_obj.stem,
            'suffix': path_obj.suffix,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'accessed': stat.st_atime,
            'is_file': path_obj.is_file(),
            'is_dir': path_obj.is_dir(),
            'absolute_path': str(path_obj.absolute()),
            'parent': str(path_obj.parent)
        }
        
    except Exception as e:
        logger.error(f"Failed to get metadata for {file_path}: {e}")
        return {}


def cleanup_directory(directory: str, pattern: str = "*", days_old: int = 7) -> Dict[str, Any]:
    """
    Clean up files in directory older than specified days.
    
    Args:
        directory: Directory to clean
        pattern: File pattern to match
        days_old: Files older than this will be deleted
        
    Returns:
        Dict with cleanup results
    """
    try:
        import time
        cutoff_time = time.time() - (days_old * 24 * 3600)
        
        directory_path = Path(directory)
        if not directory_path.exists():
            return {'success': False, 'error': 'Directory does not exist'}
        
        cleaned_files = 0
        freed_space = 0
        
        for file_path in directory_path.glob(pattern):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_size = file_path.stat().st_size
                file_path.unlink()
                cleaned_files += 1
                freed_space += file_size
                logger.info(f"Cleaned up old file: {file_path}")
        
        return {
            'success': True,
            'cleaned_files': cleaned_files,
            'freed_space_mb': round(freed_space / (1024 * 1024), 2),
            'directory': directory,
            'cutoff_days': days_old
        }
        
    except Exception as e:
        logger.error(f"Directory cleanup failed for {directory}: {e}")
        return {
            'success': False,
            'error': str(e),
            'directory': directory
        }


def get_directory_size(directory: str) -> Dict[str, Any]:
    """
    Get total size of directory and file count.
    
    Args:
        directory: Directory path
        
    Returns:
        Dict with directory statistics
    """
    try:
        directory_path = Path(directory)
        if not directory_path.exists():
            return {'success': False, 'error': 'Directory does not exist'}
        
        total_size = 0
        file_count = 0
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            'success': True,
            'directory': directory,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count
        }
        
    except Exception as e:
        logger.error(f"Failed to get directory size for {directory}: {e}")
        return {
            'success': False,
            'error': str(e),
            'directory': directory
        }


async def create_temp_file(suffix: str = '', prefix: str = 'tmp') -> str:
    """
    Create a temporary file and return its path.
    
    Args:
        suffix: File suffix/extension
        prefix: File prefix
        
    Returns:
        Path to temporary file
    """
    import tempfile
    
    try:
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)  # Close the file descriptor
        
        logger.debug(f"Created temporary file: {temp_path}")
        return temp_path
        
    except Exception as e:
        logger.error(f"Failed to create temporary file: {e}")
        raise


def is_video_file(file_path: str) -> bool:
    """
    Check if file is a video file based on extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file appears to be a video file
    """
    video_extensions = {
        'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 
        'm4v', '3gp', 'mpg', 'mpeg', 'ogv', 'ts', 'mts'
    }
    
    extension = get_file_extension(file_path).lower()
    return extension in video_extensions


def is_audio_file(file_path: str) -> bool:
    """
    Check if file is an audio file based on extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file appears to be an audio file
    """
    audio_extensions = {
        'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'opus',
        'm4a', 'ape', 'ac3', 'dts', 'aiff', 'au', 'ra'
    }
    
    extension = get_file_extension(file_path).lower()
    return extension in audio_extensions


def is_image_file(file_path: str) -> bool:
    """
    Check if file is an image file based on extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file appears to be an image file
    """
    image_extensions = {
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif',
        'webp', 'svg', 'ico', 'psd', 'raw', 'cr2', 'nef'
    }
    
    extension = get_file_extension(file_path).lower()
    return extension in image_extensions


def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory_path: Directory path to ensure (string format)
    """
    ensure_directory(Path(directory_path))


def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate file hash.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, md5, etc.)
        
    Returns:
        Hex digest of file hash
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If algorithm is not supported
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Create hash object
    if algorithm.lower() == 'md5':
        hash_obj = hashlib.md5()
    elif algorithm.lower() == 'sha256':
        hash_obj = hashlib.sha256()
    elif algorithm.lower() == 'sha1':
        hash_obj = hashlib.sha1()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    # Read file in chunks to handle large files
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        raise