"""
Main API router for v1 endpoints.

This module aggregates all API v1 routes and provides a single
router for the main application.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import jobs, videos, health

api_router = APIRouter()

# Include individual route modules
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])