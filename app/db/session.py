from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.database import Base

# Async database connection
database = Database(settings.database_url)

# Async SQLAlchemy engine
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Async session maker
AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

metadata = MetaData()


async def get_database() -> Database:
    """Dependency to get database connection"""
    return database


async def get_db_session() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await database.disconnect()
    await async_engine.dispose()