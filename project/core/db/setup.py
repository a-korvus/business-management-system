"""Main database settings."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from project.config import settings

async_engine: AsyncEngine = create_async_engine(
    url=settings.DB.url_async,
    echo=False,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides asynchronous SQLAlchemy database session.

    Yields:
        AsyncSession: SQLAlchemy AsyncSession instance for database operations.
    """
    async with AsyncSessionFactory() as session:
        yield session
