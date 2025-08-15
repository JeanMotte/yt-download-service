from typing import AsyncGenerator
from urllib.parse import parse_qs, urlparse

from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from yt_download_service.app.utils.env import (
    get_or_raise_env,
)

# Use your method for getting the database URL
DB_URL = get_or_raise_env("DB_URL")

# Parse URL, as neondb gives extra params that are not compatible with sqlalchemy
# when extracting docker images
parsed_url = urlparse(DB_URL)
query_params = parse_qs(parsed_url.query)

parsed_args = {k: v[0] for k, v in query_params.items()}
connect_args = {}

# Keep the 'options' parameter if it exists, as it's often critical.
if "options" in parsed_args:
    connect_args["options"] = parsed_args["options"]

# Translate the 'sslmode' parameter for the asyncpg driver.
if parsed_args.get("sslmode") == "require":
    connect_args["ssl"] = True

clean_db_url = parsed_url._replace(query=None).geturl()

# 1. Use create_async_engine
engine = create_async_engine(
    clean_db_url,
    connect_args=connect_args,
    poolclass=AsyncAdaptedQueuePool,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=True,
)

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
