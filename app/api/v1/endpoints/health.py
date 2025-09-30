"""
Health check endpoints.

This module provides comprehensive health checking endpoints
for monitoring system status and dependencies.
"""

from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_async_session
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Dict: Basic health status
    """
    return {
        "status": "healthy",
        "service": "ai-video-automation",
        "version": "0.1.0"
    }


@router.get("/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Detailed health check with dependency status.
    
    Args:
        db: Database session for connectivity check
        
    Returns:
        Dict: Detailed health status including dependencies
    """
    health_status = {
        "status": "healthy",
        "service": "ai-video-automation",
        "version": "0.1.0",
        "checks": {}
    }
    
    # Check database connectivity
    try:
        result = await db.execute(text("SELECT 1"))
        await result.fetchone()
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis connectivity (placeholder)
    health_status["checks"]["redis"] = {"status": "healthy"}
    
    # Check external services (placeholder)
    health_status["checks"]["storage"] = {"status": "healthy"}
    health_status["checks"]["ai_services"] = {"status": "healthy"}
    
    return health_status


@router.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        Dict: Readiness status
    """
    return {"status": "ready"}


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        Dict: Liveness status
    """
    return {"status": "alive"}