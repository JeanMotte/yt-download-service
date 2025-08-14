from typing import AsyncGenerator

from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.yt_download_service.app.utils.env import (
    get_or_raise_env,
)

# Use your method for getting the database URL
DB_URL = get_or_raise_env("DB_URL")
clean_db_url = DB_URL.split("?")[0]
connect_args = {"ssl": "require"}

# 1. Use create_async_engine
engine = create_async_engine(
    clean_db_url,
    connect_args=connect_args,
    poolclass=AsyncAdaptedQueuePool,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=True,
)

# 2. Use async_sessionmaker for creating async sessions
AsyncSessionFactory = async_sessionmaker(
    engine, autoflush=False, expire_on_commit=False, class_=AsyncSession
)

async_session_factory = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
