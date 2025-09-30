# AI Video Automation Pipeline - FastAPI Project

## 🚀 Quick Start

This is a production-grade FastAPI application for AI-powered video content automation. The application converts viral videos into new content using AI services and publishes to multiple platforms.

## 📁 Project Structure

```
AI_VOICE_AUTOMATION/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application factory
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── logging.py         # Structured logging
│   │   └── security.py        # Authentication & security
│   ├── api/
│   │   └── v1/
│   │       ├── router.py      # Main API router
│   │       └── endpoints/     # API endpoint modules
│   ├── db/
│   │   └── session.py         # Database session management
│   ├── models/                # SQLAlchemy models (to be created)
│   ├── schemas/               # Pydantic schemas
│   │   ├── video.py          # Video-related schemas
│   │   └── job.py            # Job-related schemas
│   ├── services/              # Business logic services
│   │   ├── ingest/           # Video ingestion services
│   │   ├── transform/        # AI transformation services
│   │   ├── avatar/           # Avatar generation services
│   │   └── publish/          # Publishing services
│   ├── tasks/                # Celery tasks
│   │   ├── celery_app.py     # Celery configuration
│   │   └── video_tasks.py    # Video processing tasks
│   └── utils/                # Utility modules
│       ├── ffmpeg_processor.py # Video processing utilities
│       └── storage.py        # File storage utilities
├── tests/                    # Test suite (to be created)
├── scripts/                  # Deployment and utility scripts
├── docs/                     # Documentation
├── .env.example             # Environment variables template
├── run.py                   # Application entry point
└── PROJECT_PLAN.md          # Detailed project roadmap
```

## 🛠️ Technology Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM with PostgreSQL
- **Celery** - Distributed task queue
- **Redis** - Message broker and caching
- **Pydantic** - Data validation and serialization
- **FFmpeg** - Video processing
- **yt-dlp** - Video downloading
- **OpenAI APIs** - AI content transformation
- **ElevenLabs** - Text-to-speech
- **D-ID/Synthesia** - Avatar generation

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- FFmpeg
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI_VOICE_AUTOMATION
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Or for development
   pip install -r requirements-dev.txt
   
   # Or using the modern approach
   pip install -e .
   
   # Or using the convenience script
   python scripts/manage.py setup dev
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database** (After Task 4 completion)
   ```bash
   # Create database
   createdb ai_video_automation
   
   # Run migrations
   alembic upgrade head
   ```

6. **Start services**
   ```bash
   # Start Redis
   redis-server
   
   # Start Celery worker (in separate terminal)
   celery -A app.tasks.celery_app worker --loglevel=info
   
   # Or using the convenience script
   python scripts/manage.py dev worker
   
   # Start FastAPI application
   python run.py
   
   # Or using the convenience script  
   python scripts/manage.py dev run
   ```

## 🛠️ Development Tools

The project includes several convenience tools:

### Management CLI
```bash
# Setup development environment
python scripts/manage.py setup dev

# Run development server
python scripts/manage.py dev run

# Run tests with coverage
python scripts/manage.py test run --cov

# Check code quality
python scripts/manage.py lint check

# Fix code formatting
python scripts/manage.py lint fix

# Show project status
python scripts/manage.py status
```

### Make Commands
```bash
# Setup development environment
make dev-setup

# Run development server
make run-dev

# Run tests with coverage
make test-cov

# Format code
make format

# Run linting
make lint

# Start with Docker
make docker-run
```

## 📋 Current Implementation Status

✅ **Task 1: FastAPI Project Scaffold** - COMPLETED
✅ **Task 2: Set up core dependencies and config** - COMPLETED
- ✅ Production-grade directory structure
- ✅ FastAPI application with async architecture
- ✅ Core configuration management
- ✅ Structured logging system
- ✅ API routing and endpoints structure
- ✅ Pydantic schemas for validation
- ✅ Celery task queue setup
- ✅ Service layer architecture
- ✅ Utility modules (FFmpeg, Storage)
- ✅ Environment configuration
- ✅ Modern Python packaging (pyproject.toml)
- ✅ Development tools (Makefile, CLI, pre-commit)
- ✅ Docker configuration for development
- ✅ Database session management
- ✅ Code quality tools and linting setup

🔄 **Next: Task 3** - Create Pydantic models and schemas
🔄 **Next: Task 4** - Set up database layer with SQLAlchemy

## 🏗️ Architecture Overview

The application follows a clean architecture pattern with clear separation of concerns:

- **API Layer**: FastAPI routes with request/response handling
- **Service Layer**: Business logic and external service integration
- **Data Layer**: Database models and data access
- **Task Layer**: Async background processing with Celery
- **Utility Layer**: Shared utilities and helper functions

## 🔧 Development Guidelines

### Code Quality
- Follow PEP 8 and use Black formatting
- Use type hints throughout
- Write comprehensive docstrings
- Implement proper error handling
- Maintain test coverage >90%

### Security
- Store secrets in environment variables
- Use proper authentication and authorization
- Implement rate limiting
- Validate and sanitize all inputs
- Regular security dependency updates

### Performance
- Use async/await for I/O operations
- Implement connection pooling
- Cache frequently accessed data
- Optimize database queries
- Monitor and profile performance

## 📊 API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py
```

## 📦 Deployment

### Docker (Recommended)
```bash
# Build image
docker build -t ai-video-automation .

# Run with docker-compose
docker-compose up -d
```

### Production Deployment
- Use proper secrets management
- Set up monitoring and logging
- Configure load balancing
- Implement health checks
- Set up backup strategies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the PROJECT_PLAN.md for detailed roadmap
- Review the API documentation
- Check existing issues in the repository
- Create a new issue for bugs or feature requests

---

**Next Steps**: Complete Task 2 (dependencies and config) to continue with the implementation roadmap.