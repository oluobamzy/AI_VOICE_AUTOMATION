#!/usr/bin/env python3
"""
CLI tool for AI Video Automation Pipeline
"""

import typer
import asyncio
from pathlib import Path
from app.core.config import settings
from app.core.logging import setup_logging, logger

app = typer.Typer()


@app.command()
def start_server(
    host: str = typer.Option(settings.host, help="Host to bind to"),
    port: int = typer.Option(settings.port, help="Port to bind to"),
    reload: bool = typer.Option(settings.debug, help="Enable auto-reload"),
    workers: int = typer.Option(settings.workers, help="Number of worker processes")
):
    """Start the FastAPI server"""
    import uvicorn
    
    setup_logging()
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1
    )


@app.command()
def start_worker(
    loglevel: str = typer.Option("info", help="Log level"),
    queues: str = typer.Option("default", help="Comma-separated list of queues")
):
    """Start Celery worker"""
    import subprocess
    
    cmd = [
        "celery", "-A", "app.core.celery_app", "worker",
        "--loglevel", loglevel,
        "--queues", queues
    ]
    
    logger.info(f"Starting Celery worker: {' '.join(cmd)}")
    subprocess.run(cmd)


@app.command()
def init_db():
    """Initialize database tables"""
    async def _init_db():
        from app.db.session import init_db
        await init_db()
        logger.info("Database initialized successfully")
    
    setup_logging()
    asyncio.run(_init_db())


@app.command()
def cleanup_temp():
    """Clean up temporary files"""
    from app.utils.helpers import cleanup_temp_files
    
    setup_logging()
    cleanup_temp_files(settings.temp_video_dir)
    logger.info("Temporary files cleaned up")


if __name__ == "__main__":
    app()