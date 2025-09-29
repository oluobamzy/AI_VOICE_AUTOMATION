from fastapi import APIRouter, status
from datetime import datetime
from app.models.schemas import HealthCheck
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        try:
            from app.db.session import database
            await database.fetch_one("SELECT 1")
            db_status = "healthy"
        except:
            db_status = "unhealthy"
        
        # Check Redis connection
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
            redis_status = "healthy"
        except:
            redis_status = "unhealthy"
        
        # Check Celery
        try:
            from app.core.celery_app import celery_app
            celery_inspect = celery_app.control.inspect()
            active_tasks = celery_inspect.active()
            celery_status = "healthy" if active_tasks is not None else "unhealthy"
        except:
            celery_status = "unhealthy"
        
        services = {
            "database": db_status,
            "redis": redis_status,
            "celery": celery_status
        }
        
        overall_status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"
        
        return HealthCheck(
            status=overall_status,
            version=settings.version,
            timestamp=datetime.utcnow(),
            services=services
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="unhealthy",
            version=settings.version,
            timestamp=datetime.utcnow(),
            services={"error": str(e)}
        )


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    try:
        # Basic readiness checks
        from app.db.session import database
        await database.fetch_one("SELECT 1")
        
        return {"status": "ready"}
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not ready", "error": str(e)}


@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {"status": "alive"}