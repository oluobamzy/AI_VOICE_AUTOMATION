import os
import hashlib
import uuid
from pathlib import Path
from typing import Optional, Union
from datetime import datetime


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """Generate unique filename with timestamp and hash"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_hash = hashlib.md5(f"{original_filename}{uuid.uuid4()}".encode()).hexdigest()[:8]
    
    name, ext = os.path.splitext(original_filename)
    return f"{prefix}{timestamp}_{file_hash}{ext}"


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes"""
    return os.path.getsize(file_path) / (1024 * 1024)


def cleanup_temp_files(directory: str, older_than_hours: int = 24):
    """Clean up temporary files older than specified hours"""
    import time
    
    if not os.path.exists(directory):
        return
    
    current_time = time.time()
    cutoff_time = current_time - (older_than_hours * 3600)
    
    for file_path in Path(directory).glob("*"):
        if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
            try:
                file_path.unlink()
            except OSError:
                pass  # File might be in use


def validate_url(url: str) -> bool:
    """Basic URL validation"""
    from urllib.parse import urlparse
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem safety"""
    import re
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    filename = filename.strip('. ')
    # Ensure not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename