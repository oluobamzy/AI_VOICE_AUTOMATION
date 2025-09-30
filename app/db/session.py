"""
Database session management.

This moduasync def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides async database session.
    
    Yields:
        AsyncSession: Database session for dependency injection
        
    Example:
        @app.get("/items/")
        async def read_items(db: AsyncSession = Depends(get_async_session)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()c database sessions, connection pooling,
and provides dependency injection for FastAPI routes.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# Create async engine with connection pooling
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides async database session.
    
    Yields:
        AsyncSession: Database session for dependency injection
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


async def drop_tables():
    """Drop all database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {str(e)}")
        raise


async def init_database() -> None:
    """
    Initialize database connection and create tables.
    
    This function should be called during application startup.
    """
    try:
        # Test database connection
        async with engine.begin() as conn:
            # Import all models to ensure they are registered
            try:
                from app.models import *  # noqa: F403, F401
            except ImportError:
                logger.warning("Models not yet created - skipping model import")
            
            # Create all tables (in production, use Alembic migrations instead)
            if settings.ENVIRONMENT == "development":
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created successfully")
            
        logger.info("Database connection established successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def close_database() -> None:
    """
    Close database connections.
    
    This function should be called during application shutdown.
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")
        raise