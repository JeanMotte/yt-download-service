from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from yt_download_service.infrastructure.database import path

engine = create_engine(path.SQLALCHEMY_DATABASE_URL)
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Any, Any, Any] | None:
    """Dependency to get a database session."""
    db = SessionFactory()

    try:
        yield db
    finally:
        db.close()
