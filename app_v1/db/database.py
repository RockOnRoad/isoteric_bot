"""Database connection and session management."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from core.config import settings


# Create async engine with connection pool settings
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Maximum number of connections beyond pool_size
    pool_timeout=30,  # Seconds to wait before giving up on getting a connection
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before using them
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session():
    """Get database session generator."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
