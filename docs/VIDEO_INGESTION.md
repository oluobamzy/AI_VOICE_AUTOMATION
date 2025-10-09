# Video Ingestion Service

This document describes the comprehensive video ingestion system implemented for the AI Video Automation pipeline.

## Overview

The video ingestion service provides a complete solution for downloading, validating, and processing videos from various social media platforms. It includes support for single video ingestion, batch processing, URL validation, and comprehensive error handling.

## Architecture

### Core Components

1. **VideoDownloader**: Low-level video downloading using yt-dlp
2. **URLValidator**: Comprehensive URL validation and security checks
3. **VideoIngestionService**: High-level ingestion orchestration
4. **BatchVideoIngestionService**: Batch processing with concurrency control

### Service Flow

```
URL Input → Validation → Metadata Extraction → Content Validation → Download → Storage → Thumbnail
```

## Features

### Platform Support

- **TikTok**: `tiktok.com`, `vm.tiktok.com`
- **YouTube**: `youtube.com`, `youtu.be`, YouTube Shorts
- **Instagram**: Posts, Reels, IGTV
- **Twitter/X**: `twitter.com`, `x.com`
- **Facebook**: `facebook.com`, `fb.watch`

### Advanced Capabilities

- **Platform-specific optimization**: Tailored download settings per platform
- **Metadata extraction**: Comprehensive video metadata without downloading
- **Content validation**: Duration, keyword, and quality checks
- **Batch processing**: Concurrent processing of multiple videos
- **Error recovery**: Automatic retry with exponential backoff
- **Security validation**: Malicious URL detection and blocking
- **Thumbnail extraction**: Automatic thumbnail download
- **Storage management**: Organized file storage with cleanup

## Usage Examples

### Single Video Ingestion

```python
from app.services.ingest import VideoIngestionService

# Initialize service
ingestion_service = VideoIngestionService()

# Ingest a single video
result = await ingestion_service.ingest_video(
    url="https://www.tiktok.com/@user/video/123",
    user_id="user123",
    options={
        "quality": "high",
        "download_subtitles": True,
        "min_duration": 5,
        "max_duration": 300
    }
)

print(f"Success: {result['success']}")
print(f"Video path: {result['video_path']}")
print(f"Thumbnail: {result['thumbnail_path']}")
```

### Batch Video Ingestion

```python
from app.services.ingest import BatchVideoIngestionService

# Initialize batch service
batch_service = BatchVideoIngestionService(max_concurrent=5)

# Start batch ingestion
urls = [
    "https://www.tiktok.com/@user1/video/123",
    "https://www.youtube.com/watch?v=abc123",
    "https://www.instagram.com/p/def456/"
]

job_id = await batch_service.start_batch_ingestion(
    urls=urls,
    user_id="user123",
    options={"quality": "medium"}
)

# Monitor progress
status = batch_service.get_batch_status(job_id)
print(f"Progress: {status['progress']}%")
print(f"Successful: {status['successful_videos']}")
print(f"Failed: {status['failed_videos']}")
```

### URL Validation

```python
from app.services.ingest import URLValidator

# Initialize validator
validator = URLValidator()

# Validate URL
result = await validator.validate_url(
    url="https://www.tiktok.com/@user/video/123",
    check_accessibility=True
)

print(f"Valid: {result['is_valid']}")
print(f"Platform: {result['platform']}")
print(f"Errors: {result['errors']}")
```

### Metadata Extraction

```python
from app.services.ingest import VideoDownloader

# Initialize downloader
downloader = VideoDownloader()

# Extract metadata without downloading
metadata = await downloader.extract_metadata(
    "https://www.youtube.com/watch?v=abc123"
)

print(f"Title: {metadata.title}")
print(f"Duration: {metadata.duration} seconds")
print(f"Resolution: {metadata.resolution}")
print(f"View count: {metadata.view_count}")
```

## Configuration

### Environment Variables

```bash
# Storage configuration
UPLOAD_DIR=/app/storage

# Download settings
DOWNLOAD_TIMEOUT=300
MAX_FILE_SIZE=500MB
MAX_CONCURRENT_DOWNLOADS=5

# Platform-specific settings
TIKTOK_MAX_DURATION=600
YOUTUBE_MAX_DURATION=900
INSTAGRAM_MAX_DURATION=300
```

### Platform Configurations

The service includes platform-specific configurations for optimal downloading:

```python
PLATFORM_CONFIGS = {
    'tiktok': {
        'format': 'best[height<=1080]/best',
        'writesubtitles': False,
        'max_duration': 600
    },
    'youtube': {
        'format': 'best[height<=1080]/best',
        'writesubtitles': True,
        'writeautomaticsub': True,
        'max_duration': 900
    },
    # ... other platforms
}
```

## API Reference

### VideoIngestionService

#### `ingest_video(url, user_id, options=None)`

Complete video ingestion pipeline.

**Parameters:**
- `url` (str): Video URL to ingest
- `user_id` (str): User identifier
- `options` (dict, optional): Ingestion options

**Returns:**
- `Dict[str, Any]`: Ingestion results with success status, paths, and metadata

**Options:**
- `quality`: Download quality ('low', 'medium', 'high', 'best')
- `download_subtitles`: Whether to download subtitles (bool)
- `min_duration`: Minimum video duration in seconds
- `max_duration`: Maximum video duration in seconds
- `required_keywords`: List of required keywords in title/description
- `blocked_keywords`: List of blocked keywords

### BatchVideoIngestionService

#### `start_batch_ingestion(urls, user_id, options=None)`

Start batch video ingestion job.

**Parameters:**
- `urls` (List[str]): List of video URLs
- `user_id` (str): User identifier
- `options` (dict, optional): Batch options

**Returns:**
- `str`: Batch job ID for tracking

#### `get_batch_status(job_id)`

Get batch job status and progress.

**Parameters:**
- `job_id` (str): Batch job identifier

**Returns:**
- `Dict[str, Any]`: Job status, progress, and statistics

### URLValidator

#### `validate_url(url, check_accessibility=True)`

Comprehensive URL validation.

**Parameters:**
- `url` (str): URL to validate
- `check_accessibility` (bool): Whether to check URL accessibility

**Returns:**
- `Dict[str, Any]`: Validation results with errors and metadata

### VideoDownloader

#### `download_video(url, options=None, extract_metadata=True)`

Download video with options.

**Parameters:**
- `url` (str): Video URL
- `options` (dict, optional): yt-dlp options
- `extract_metadata` (bool): Whether to extract metadata

**Returns:**
- `Dict[str, Any]`: Download results and metadata

#### `extract_metadata(url)`

Extract video metadata without downloading.

**Parameters:**
- `url` (str): Video URL

**Returns:**
- `VideoMetadata`: Comprehensive video metadata

## Error Handling

### Error Types

1. **Validation Errors**: Invalid URLs, unsupported platforms
2. **Download Errors**: Network issues, file not found, rate limiting
3. **Storage Errors**: Disk space, permissions, file system issues
4. **Content Errors**: Duration limits, blocked content, quality issues

### Retry Strategy

- **Exponential backoff**: Increasing delays between retries
- **Maximum retries**: Configurable retry limits per error type
- **Rate limiting**: Automatic handling of platform rate limits
- **Graceful degradation**: Fallback to lower quality when needed

### Error Response Format

```json
{
    "success": false,
    "error": "Download failed: Network timeout",
    "step": "download",
    "retry_count": 2,
    "original_url": "https://...",
    "timestamp": "2025-09-30T12:00:00Z"
}
```

## Security

### URL Security

- **Domain validation**: Blocked malicious domains
- **Pattern detection**: Suspicious URL patterns
- **Protocol validation**: Only HTTP/HTTPS allowed
- **Length limits**: Maximum URL length enforcement

### Content Security

- **File type validation**: Ensure downloaded files are videos
- **Size limits**: Maximum file size enforcement  
- **Virus scanning**: Integration ready for antivirus scanning
- **Content filtering**: Keyword-based content filtering

### Data Protection

- **User isolation**: Files stored in user-specific directories
- **Access control**: Proper file permissions
- **Cleanup policies**: Automatic deletion of old files
- **Audit logging**: Comprehensive operation logging

## Performance

### Optimization Features

- **Concurrent downloads**: Configurable concurrency limits
- **Platform-specific settings**: Optimized per platform
- **Caching**: URL validation result caching
- **Streaming downloads**: Memory-efficient large file handling
- **Compression**: Efficient storage utilization

### Monitoring Metrics

- **Download speed**: Average download rates
- **Success rates**: Platform-specific success metrics
- **Error distribution**: Common error types and frequencies
- **Resource usage**: CPU, memory, and disk utilization
- **Queue depths**: Batch processing queue statistics

## Testing

### Test Coverage

- **Unit tests**: Individual component testing
- **Integration tests**: End-to-end workflow testing
- **Error scenario tests**: Comprehensive error handling
- **Performance tests**: Load and stress testing
- **Security tests**: Malicious input validation

### Running Tests

```bash
# Run comprehensive ingestion tests
python test_video_ingestion.py

# Test specific components
python -m pytest tests/test_video_downloader.py
python -m pytest tests/test_url_validator.py
python -m pytest tests/test_batch_ingestion.py
```

## Deployment

### Production Setup

1. **Dependencies**: Install yt-dlp, ffmpeg, and system dependencies
2. **Storage**: Configure persistent storage with adequate space
3. **Monitoring**: Set up logging and monitoring systems
4. **Scaling**: Configure worker processes and concurrency
5. **Security**: Implement rate limiting and security policies

### Docker Configuration

```dockerfile
# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl

# Install yt-dlp
RUN pip install yt-dlp

# Configure storage
VOLUME ["/app/storage"]
```

### Environment Setup

```bash
# Create necessary directories
mkdir -p /app/storage/{downloads,temp,thumbnails,ingested}

# Set permissions
chown -R app:app /app/storage
chmod -R 755 /app/storage

# Configure worker processes
export MAX_CONCURRENT_DOWNLOADS=5
export WORKER_PROCESSES=4
```

## Troubleshooting

### Common Issues

1. **yt-dlp outdated**: Regular updates required for platform support
2. **Rate limiting**: Implement delays and retry strategies  
3. **Storage space**: Monitor disk usage and implement cleanup
4. **Network timeouts**: Configure appropriate timeout values
5. **Platform changes**: Monitor for platform API/format changes

### Debug Tools

```python
# Enable debug logging
import logging
logging.getLogger('app.services.ingest').setLevel(logging.DEBUG)

# Test individual components
from app.services.ingest import VideoDownloader
downloader = VideoDownloader()
result = await downloader.validate_url("https://...")

# Check service statistics
from app.services.ingest import VideoIngestionService
service = VideoIngestionService()
stats = await service.get_ingestion_stats()
```

### Log Analysis

```bash
# Filter ingestion logs
grep "video_ingestion" /var/log/app.log

# Check error patterns
grep "ERROR.*ingest" /var/log/app.log | awk '{print $5}' | sort | uniq -c

# Monitor success rates
grep "ingestion completed" /var/log/app.log | wc -l
```

## Best Practices

### Performance

- Use batch ingestion for multiple videos
- Configure appropriate concurrency limits
- Implement proper cleanup policies
- Monitor resource usage continuously

### Security

- Validate all input URLs thoroughly
- Implement rate limiting per user
- Use secure file storage practices
- Regular security updates for dependencies

### Reliability

- Implement comprehensive error handling
- Use exponential backoff for retries
- Monitor service health continuously
- Maintain audit logs for troubleshooting

### Scalability

- Design for horizontal scaling
- Use proper queue management
- Implement load balancing
- Monitor and optimize bottlenecks