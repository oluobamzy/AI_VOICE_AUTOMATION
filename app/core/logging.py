"""
Structured logging configuration.

This module sets up structured logging with JSON formatting,
correlation IDs, and integration with monitoring systems.
"""

import logging
import logging.config
import sys
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # In a real application, you'd get this from context (e.g., from FastAPI request)
        record.correlation_id = getattr(record, 'correlation_id', 'no-correlation-id')
        return True


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Custom formatter for JSON logging
    json_formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(correlation_id)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console formatter for development
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(correlation_id)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure logging
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation": {
                "()": CorrelationFilter,
            },
        },
        "formatters": {
            "json": {
                "()": jsonlogger.JsonFormatter,
                "format": "%(asctime)s %(name)s %(levelname)s %(correlation_id)s %(message)s"
            },
            "console": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(correlation_id)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "console" if settings.ENVIRONMENT == "development" else "json",
                "filters": ["correlation"],
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "celery": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }
    
    logging.config.dictConfig(logging_config)
    
    # Set up specific loggers
    logger = logging.getLogger("app")
    logger.info("Logging configured", extra={"environment": settings.ENVIRONMENT})


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(f"app.{name}")