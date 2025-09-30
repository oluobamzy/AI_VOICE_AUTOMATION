# AI Video Automation Pipeline - Development Makefile
# Use: make <command>

.PHONY: help install install-dev install-prod clean test test-cov lint format run run-worker run-dev migrate migrate-create migrate-upgrade migrate-downgrade docker-build docker-run docker-dev

# Default help command
help:
	@echo "AI Video Automation Pipeline - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  install-prod   Install production dependencies"
	@echo "  clean          Clean up temporary files and caches"
	@echo ""
	@echo "Development Commands:"
	@echo "  run            Run the FastAPI server"
	@echo "  run-dev        Run the server in development mode with reload"
	@echo "  run-worker     Run Celery worker"
	@echo "  format         Format code with black and isort"
	@echo "  lint           Run linting with flake8 and mypy"
	@echo "  test           Run tests"
	@echo "  test-cov       Run tests with coverage report"
	@echo ""
	@echo "Database Commands:"
	@echo "  migrate        Show migration status"
	@echo "  migrate-create Create new migration"
	@echo "  migrate-upgrade Run database migrations"
	@echo "  migrate-downgrade Downgrade database migrations"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-run     Run with Docker Compose"
	@echo "  docker-dev     Run development environment with Docker"

# Installation commands
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

install-prod:
	pip install -r requirements-prod.txt

# Development environment setup
setup-dev: install-dev
	pre-commit install
	@echo "Development environment setup complete!"

# Clean up temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/

# Code formatting
format:
	black app/ tests/
	isort app/ tests/

# Linting
lint:
	flake8 app/ tests/
	mypy app/
	black --check app/ tests/
	isort --check-only app/ tests/

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-api:
	pytest tests/api/ -v

# Application commands
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

run-dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

run-worker:
	celery -A app.tasks.celery_app worker --loglevel=info

run-beat:
	celery -A app.tasks.celery_app beat --loglevel=info

run-flower:
	celery -A app.tasks.celery_app flower

# Database commands
migrate:
	alembic current
	alembic history

migrate-create:
	@read -p "Enter migration message: " message; \
	alembic revision --autogenerate -m "$$message"

migrate-upgrade:
	alembic upgrade head

migrate-downgrade:
	alembic downgrade -1

db-reset:
	alembic downgrade base
	alembic upgrade head

# Docker commands
docker-build:
	docker build -t ai-video-automation .

docker-run:
	docker-compose up -d

docker-dev:
	docker-compose -f docker-compose.dev.yml up

docker-stop:
	docker-compose down

docker-clean:
	docker-compose down --volumes --remove-orphans
	docker system prune -f

# Security scanning
security-scan:
	bandit -r app/
	safety check

# Documentation
docs-serve:
	mkdocs serve

docs-build:
	mkdocs build

# Environment setup
env-setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created from .env.example"; \
		echo "Please edit .env with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

# Full development setup
dev-setup: env-setup install-dev setup-dev
	@echo "Development environment ready!"
	@echo "Don't forget to:"
	@echo "1. Edit .env with your configuration"
	@echo "2. Set up PostgreSQL and Redis"
	@echo "3. Run 'make migrate-upgrade' to create database tables"

# Production deployment preparation
prod-check: lint test security-scan
	@echo "Production readiness check passed!"