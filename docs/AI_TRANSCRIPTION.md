# AI Transcription Service Documentation

## Overview

The AI Transcription Service provides comprehensive audio-to-text transcription capabilities using OpenAI's Whisper API. It supports multiple languages, speaker identification, audio preprocessing, and seamless integration with the video processing pipeline.

## Features

### Core Transcription
- **Multi-language Support**: 20+ languages with automatic detection
- **High Accuracy**: OpenAI Whisper API with confidence scoring
- **Time Segmentation**: Word and sentence-level timestamps
- **Multiple Formats**: Support for various audio/video formats

### Advanced Processing
- **Speaker Identification**: Basic speaker diarization capabilities
- **Audio Optimization**: Automatic preprocessing for better transcription
- **Batch Processing**: Concurrent transcription of multiple files
- **Language Detection**: Automatic language identification

### Integration Features
- **Database Integration**: Automatic storage of transcription results
- **Celery Tasks**: Asynchronous processing with retry logic
- **Video Processing**: Direct extraction and transcription from video
- **Error Handling**: Comprehensive error recovery and logging

## Architecture

```
┌─────────────────────┐
│   Video/Audio       │
│   Input Files       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Audio Processor    │
│  - Extract audio    │
│  - Optimize format  │
│  - Preprocessing    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Transcription       │
│ Service             │
│ - OpenAI Whisper    │
│ - Language detect   │
│ - Segmentation      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Database Storage   │
│  - Transcription    │
│  - Metadata         │
│  - Relationships    │
└─────────────────────┘
```

## API Reference

### TranscriptionService

#### Primary Methods

##### `transcribe_audio()`
```python
async def transcribe_audio(
    self,
    audio_file: BinaryIO,
    language: Optional[str] = None,
    model: str = "whisper-1",
    prompt: Optional[str] = None,
    temperature: float = 0.0,
    response_format: str = "verbose_json",
    timestamp_granularities: List[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `audio_file`: Binary audio file stream
- `language`: Target language code (auto-detect if None)
- `model`: Whisper model ("whisper-1", "whisper-large")
- `prompt`: Optional context prompt for better accuracy
- `temperature`: Sampling temperature (0.0-1.0)
- `response_format`: Output format ("json", "text", "srt", "verbose_json", "vtt")
- `timestamp_granularities`: Timestamp precision (["word", "segment"])

**Returns:**
```python
{
    "text": "Full transcribed text",
    "language": "en",
    "duration": 120.5,
    "segments": [...],
    "words": [...],
    "confidence": 0.95,
    "word_count": 245,
    "processing_time": 15.2
}
```

##### `transcribe_video_audio()`
```python
async def transcribe_video_audio(
    self,
    video_path: str,
    language: Optional[str] = None,
    model: str = "whisper-1"
) -> Dict[str, Any]
```

Extracts audio from video and transcribes it.

##### `detect_language()`
```python
async def detect_language(
    self,
    audio_file: BinaryIO
) -> Tuple[str, float]
```

Returns detected language code and confidence score.

##### `transcribe_with_speakers()`
```python
async def transcribe_with_speakers(
    self,
    audio_file: BinaryIO,
    language: Optional[str] = None
) -> Dict[str, Any]
```

Transcribes with basic speaker identification.

##### `batch_transcribe()`
```python
async def batch_transcribe(
    self,
    audio_files: List[Tuple[str, BinaryIO]],
    language: Optional[str] = None,
    model: str = "whisper-1",
    max_concurrent: int = 3
) -> List[Dict[str, Any]]
```

Processes multiple audio files concurrently.

### AudioProcessor

#### Primary Methods

##### `extract_audio_from_video()`
```python
async def extract_audio_from_video(
    self,
    video_path: str,
    output_format: str = "wav",
    sample_rate: int = 16000
) -> str
```

Extracts audio from video files with optimal settings for transcription.

##### `optimize_for_transcription()`
```python
async def optimize_for_transcription(
    self,
    audio_path: str,
    target_format: str = "wav",
    sample_rate: int = 16000,
    remove_noise: bool = True
) -> str
```

Optimizes audio for better transcription accuracy:
- Converts to mono
- Applies noise filtering
- Normalizes audio levels
- Sets optimal sample rate

##### `get_audio_info()`
```python
async def get_audio_info(
    self,
    audio_path: str
) -> Dict[str, Any]
```

Returns comprehensive audio metadata.

## Celery Tasks

### Core Tasks

#### `transcribe_video_task`
```python
transcribe_video_task.delay(
    video_id="uuid",
    video_path="/path/to/video.mp4",
    language="en",
    model="whisper-1"
)
```

#### `transcribe_audio_task`
```python
transcribe_audio_task.delay(
    audio_path="/path/to/audio.wav",
    language="en",
    model="whisper-1"
)
```

#### `detect_language_task`
```python
detect_language_task.delay(
    audio_path="/path/to/audio.wav"
)
```

#### `batch_transcribe_task`
```python
batch_transcribe_task.delay(
    audio_files_info=[
        {"filename": "file1.wav", "path": "/path/to/file1.wav"},
        {"filename": "file2.wav", "path": "/path/to/file2.wav"}
    ],
    language="en",
    max_concurrent=3
)
```

## Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Audio Processing
FFMPEG_BINARY=ffmpeg
FFPROBE_BINARY=ffprobe

# File Storage
UPLOAD_DIR=/tmp/ai_video_automation/uploads
PROCESSED_DIR=/tmp/ai_video_automation/processed

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### Supported Languages

| Code | Language    | Code | Language   |
|------|-------------|------|------------|
| en   | English     | es   | Spanish    |
| fr   | French      | de   | German     |
| it   | Italian     | pt   | Portuguese |
| ru   | Russian     | ja   | Japanese   |
| ko   | Korean      | zh   | Chinese    |
| ar   | Arabic      | hi   | Hindi      |
| nl   | Dutch       | sv   | Swedish    |
| pl   | Polish      | tr   | Turkish    |
| cs   | Czech       | da   | Danish     |
| fi   | Finnish     | no   | Norwegian  |

## Usage Examples

### Basic Transcription

```python
from app.services.ai.transcription import TranscriptionService

service = TranscriptionService()

# Transcribe audio file
with open("audio.wav", "rb") as audio_file:
    result = await service.transcribe_audio(
        audio_file=audio_file,
        language="en",
        model="whisper-1"
    )

print(f"Transcription: {result['text']}")
print(f"Confidence: {result['confidence']}")
```

### Video Transcription

```python
# Transcribe video directly
result = await service.transcribe_video_audio(
    video_path="/path/to/video.mp4",
    language="en"
)

print(f"Duration: {result['duration']}s")
print(f"Word count: {result['word_count']}")
```

### Language Detection

```python
# Detect language automatically
with open("unknown_language.wav", "rb") as audio_file:
    language, confidence = await service.detect_language(audio_file)

print(f"Detected: {language} (confidence: {confidence})")
```

### Speaker Identification

```python
# Transcribe with speaker separation
with open("conversation.wav", "rb") as audio_file:
    result = await service.transcribe_with_speakers(audio_file)

if result['has_multiple_speakers']:
    print(f"Detected {result['estimated_speaker_count']} speakers")
    for segment in result['segments_with_speakers']:
        speaker = segment['speaker']
        text = segment['text']
        print(f"Speaker {speaker}: {text}")
```

### Batch Processing

```python
# Process multiple files
audio_files = [
    ("file1.wav", open("file1.wav", "rb")),
    ("file2.wav", open("file2.wav", "rb"))
]

results = await service.batch_transcribe(
    audio_files=audio_files,
    language="en",
    max_concurrent=2
)

for result in results:
    if 'error' not in result:
        print(f"{result['filename']}: {result['text'][:50]}...")
```

## Error Handling

### Common Exceptions

- `TranscriptionError`: General transcription failures
- `AudioProcessingError`: Audio processing issues
- `ValidationError`: Invalid parameters
- `RateLimitError`: API rate limits exceeded

### Retry Logic

All tasks include automatic retry with exponential backoff:
- Audio transcription: 3 retries with 60s base delay
- Language detection: 2 retries with 30s base delay
- Batch processing: 1 retry with 120s base delay

### Error Recovery

```python
try:
    result = await service.transcribe_audio(audio_file)
except TranscriptionError as e:
    logger.error(f"Transcription failed: {e}")
    # Implement fallback or user notification
except RateLimitError as e:
    logger.warning(f"Rate limited: {e}")
    # Implement queue delay or notification
```

## Performance Optimization

### Audio Preprocessing

1. **Format Optimization**: Convert to 16kHz mono WAV
2. **Noise Reduction**: Apply high/low-pass filters
3. **Normalization**: Ensure consistent audio levels
4. **Compression**: Optimize file size while maintaining quality

### Batch Processing

1. **Concurrency Control**: Limit concurrent requests (default: 3)
2. **Memory Management**: Process files in chunks for large batches
3. **Progress Tracking**: Monitor batch completion status
4. **Error Isolation**: Continue processing despite individual failures

### Caching Strategy

1. **Result Caching**: Cache transcription results by audio hash
2. **Language Detection**: Cache detected languages
3. **Audio Info**: Cache audio metadata
4. **Cleanup**: Automatic cleanup of temporary files

## Integration Patterns

### Video Processing Pipeline

```python
# Complete video transcription workflow
async def process_video_with_transcription(video_id: str, video_path: str):
    # 1. Extract and optimize audio
    audio_processor = AudioProcessor()
    audio_path = await audio_processor.extract_audio_from_video(video_path)
    optimized_path = await audio_processor.optimize_for_transcription(audio_path)
    
    # 2. Transcribe with metadata
    service = TranscriptionService()
    with open(optimized_path, 'rb') as audio_file:
        result = await service.transcribe_audio(audio_file, response_format="verbose_json")
    
    # 3. Save to database
    transcription_manager = TranscriptionManager(db_session)
    transcription = await transcription_manager.create_transcription(
        video_id=video_id,
        audio_file_path=optimized_path,
        language=result['detected_language']
    )
    
    return transcription
```

### Celery Integration

```python
# Queue transcription task
from app.tasks.ai_tasks import transcribe_video_task

task_result = transcribe_video_task.delay(
    video_id=str(video.id),
    video_path=video.file_path,
    language="en"
)

# Monitor progress
while not task_result.ready():
    time.sleep(1)

result = task_result.get()
transcription_id = result['transcription_id']
```

## Testing

### Running Tests

```bash
# Run transcription service tests
python test_transcription_service.py

# Run with specific audio file
AUDIO_FILE=/path/to/test.wav python test_transcription_service.py
```

### Test Coverage

- ✅ Basic transcription functionality
- ✅ Language detection accuracy
- ✅ Audio processing pipeline
- ✅ Speaker identification
- ✅ Error handling and retries
- ✅ Configuration validation
- ✅ Database integration
- ✅ Celery task execution

## Monitoring and Logging

### Metrics Tracked

- Transcription success/failure rates
- Processing time distribution
- Language detection accuracy
- Audio quality metrics
- API rate limit usage
- Error frequency by type

### Log Levels

- `INFO`: Successful operations, processing times
- `WARNING`: Rate limits, quality issues
- `ERROR`: Transcription failures, API errors
- `DEBUG`: Detailed processing steps

### Example Logs

```
INFO - Starting video transcription task: 12345-67890
INFO - Extracting audio from /uploads/video.mp4 to /tmp/video_audio.wav
INFO - Audio extracted successfully: /tmp/video_audio.wav
INFO - Optimizing audio /tmp/video_audio.wav for transcription
INFO - Starting transcription with model whisper-1, language: en
INFO - Transcription completed in 15.23s
INFO - Created transcription record: abcdef-123456
INFO - Video transcription completed: 12345-67890
```

## Troubleshooting

### Common Issues

#### OpenAI API Errors
```
Error: Rate limit exceeded
Solution: Implement retry with exponential backoff (built-in)
```

#### Audio Processing Failures
```
Error: FFmpeg not found
Solution: Install ffmpeg system package
```

#### Memory Issues
```
Error: Out of memory during batch processing
Solution: Reduce max_concurrent parameter
```

#### Language Detection Issues
```
Error: Poor language detection
Solution: Provide language parameter explicitly
```

### Debug Commands

```bash
# Test OpenAI connection
python -c "from app.services.ai.transcription import TranscriptionService; print('API configured:', bool(TranscriptionService().client.api_key))"

# Check audio file info
python -c "from app.utils.audio_utils import AudioProcessor; import asyncio; print(asyncio.run(AudioProcessor().get_audio_info('file.wav')))"

# Test configuration
python -c "from app.core.config import get_settings; s = get_settings(); print('OpenAI Key:', bool(s.OPENAI_API_KEY))"
```

## Security Considerations

### API Key Management
- Store OpenAI API key in environment variables
- Use different keys for development/production
- Monitor API usage and costs
- Implement rate limiting

### Data Protection
- Audio files are processed in temporary directories
- Automatic cleanup of temporary files
- No permanent storage of sensitive audio content
- Transcription text stored securely in database

### Access Control
- Validate user permissions before transcription
- Audit trail of transcription requests
- Resource usage monitoring per user
- Rate limiting per user/API key

## Cost Optimization

### OpenAI Whisper Pricing
- Monitor API usage through OpenAI dashboard
- Implement usage alerts and limits
- Cache results to avoid re-processing
- Use audio optimization to reduce processing time

### Resource Management
- Cleanup temporary files regularly
- Monitor disk space usage
- Optimize concurrent processing limits
- Use appropriate model for accuracy vs cost balance