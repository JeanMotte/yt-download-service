from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.yt_download_service.app.utils.env import (
    get_or_raise_env,
)

# Use your method for getting the database URL
DB_URL = get_or_raise_env("DB_URL")
clean_db_url = DB_URL.split("?")[0]
connect_args = {"ssl": "require"}

# 1. Use create_async_engine
engine = create_async_engine(clean_db_url, connect_args=connect_args)

# 2. Use async_sessionmaker for creating async sessions
AsyncSessionFactory = async_sessionmaker(
    engine, autoflush=False, expire_on_commit=False, class_=AsyncSession
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    et an asynchronous database session.

    This will be injected into your route functions.
    """
    async with AsyncSessionFactory() as session:
        yield session
