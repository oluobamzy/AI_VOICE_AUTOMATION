# AI Video Automation Pipeline

A production-grade FastAPI application for automated video processing, AI avatar generation, and multi-platform publishing. This pipeline converts viral TikTok videos into YouTube Shorts and automatically publishes them to your dedicated channels.

## Features

- **Video Ingestion**: Download and validate videos from various platforms
- **Video Transformation**: Resize, compress, and optimize videos for different platforms
- **AI Avatar Generation**: Create AI-powered avatars with voice synthesis
- **Multi-Platform Publishing**: Automated publishing to YouTube, TikTok, and Instagram
- **Async Processing**: Celery-based task queue for background processing
- **FFmpeg Integration**: Professional video processing capabilities
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Production Ready**: Docker containerization, health checks, monitoring

## Architecture

```
app/
├── api/           # FastAPI routes and endpoints
├── avatar/        # AI avatar generation service
├── core/          # Core configuration and utilities
├── db/            # Database models and connections
├── ingest/        # Video ingestion from platforms
├── models/        # Pydantic data models
├── publish/       # Multi-platform publishing
├── transform/     # Video transformation and processing
├── utils/         # Utility functions and FFmpeg integration
└── tests/         # Test suites
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- FFmpeg
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/oluobamzy/AI_VOICE_AUTOMATION.git
cd AI_VOICE_AUTOMATION
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
python cli.py init-db
```

5. Start the services:
```bash
# Start the API server
python cli.py start-server

# Start Celery worker (in another terminal)
python cli.py start-worker
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run individual services
docker build -t ai-video-automation .
docker run -p 8000:8000 ai-video-automation
```

## API Usage

### Create a Video Processing Job

```bash
curl -X POST "http://localhost:8000/api/v1/videos/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Viral TikTok Video",
    "description": "Converting to YouTube Short",
    "source_url": "https://example.com/video.mp4",
    "platform": "tiktok",
    "tags": ["viral", "funny", "trending"]
  }'
```

### Process Video with AI Avatar

```bash
curl -X POST "http://localhost:8000/api/v1/processing/avatar/1" \
  -H "Content-Type: application/json" \
  -d '{
    "avatar_config": {
      "voice_id": "eleven_labs_voice_id",
      "voice_speed": 1.1,
      "avatar_style": "realistic"
    },
    "custom_script": "Welcome to this amazing video!"
  }'
```

### Publish to Platforms

```bash
curl -X POST "http://localhost:8000/api/v1/processing/publish/1" \
  -H "Content-Type: application/json" \
  -d '{
    "publish_config": {
      "platform": "youtube",
      "title": "Amazing Short Video",
      "description": "Automatically generated content",
      "tags": ["shorts", "ai", "automation"],
      "privacy_setting": "public"
    }
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `OPENAI_API_KEY` | OpenAI API key for script generation | Optional |
| `YOUTUBE_API_KEY` | YouTube Data API key | Optional |
| `TIKTOK_API_KEY` | TikTok API key | Optional |
| `FFMPEG_PATH` | Path to FFmpeg binary | `/usr/bin/ffmpeg` |
| `TEMP_VIDEO_DIR` | Temporary video storage directory | `/tmp/videos` |
| `MAX_VIDEO_SIZE_MB` | Maximum video file size in MB | `100` |

### Platform Configuration

Each platform has specific requirements:

- **YouTube Shorts**: 1080x1920 (vertical), max 60 seconds
- **TikTok**: 1080x1920 (vertical), max 10 minutes
- **Instagram Reels**: 1080x1920 (vertical), max 90 seconds

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest app/tests/test_api.py
```

### Code Quality

```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

### Development Server

```bash
# Start with auto-reload
python cli.py start-server --reload

# Start Celery worker with monitoring
python cli.py start-worker --loglevel=debug
```

## API Documentation

When running the server, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`

## Monitoring

- **Health Checks**: `/health`, `/ready`, `/live`
- **Metrics**: `/metrics` (Prometheus format)
- **Logging**: Structured JSON logging with configurable levels

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
