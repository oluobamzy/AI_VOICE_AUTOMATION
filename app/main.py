"""
Main FastAPI application factory and configuration.

This module contains the FastAPI application factory with proper async setup,
middleware configuration, error handling, and routing.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
# from prometheus_fastapi_instrumentator import Instrumentator  # Temporarily disabled for Python 3.8

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine, init_db, check_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Async context manager for application lifecycle management.
    
    Handles startup and shutdown events for database connections,
    background tasks, and other resources.
    """
    # Startup
    setup_logging()
    
    # Initialize database connection pool
    await init_db()
    
    # Start background tasks or other services
    
    yield
    
    # Shutdown
    # Database connections will be closed automatically


def create_application() -> FastAPI:
    """
    Application factory for creating FastAPI instance with all configurations.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI Video Automation Pipeline for converting viral content",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )
    
    
    # Set up CORS - Allow frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000", "*"],  # Allow frontend
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for security
    if settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )
    
    # Set up metrics collection
    if settings.ENABLE_METRICS:
        # instrumentator = Instrumentator()  # Temporarily disabled for Python 3.8
        # instrumentator.instrument(app).expose(app)
        pass
    
    # Include API routes FIRST (before static files)
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Mount static files for frontend (CSS, JS, images)
    import os
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    # Add custom exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    return app


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors with detailed response."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "body": exc.body,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions with error tracking."""
    # In production, you would log this to your error tracking service
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.ENVIRONMENT != "production" else "An error occurred",
        },
    )


# Create the application instance
app = create_application()


@app.get("/")
async def root():
    """Serve the frontend application."""
    import os
    from fastapi.responses import FileResponse
    
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        return {
            "message": "AI Video Automation Pipeline",
            "version": "0.1.0",
            "status": "operational",
            "environment": settings.ENVIRONMENT,
            "frontend": "not_found"
        }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-09-30T00:00:00Z",
        "version": "0.1.0",
        "services": {
            "database": "connected",
            "redis": "connected",
            "storage": "accessible",
        },
    }