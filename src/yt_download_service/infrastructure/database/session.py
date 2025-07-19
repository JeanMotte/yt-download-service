from typing import Generator, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from polynom_api_template.config import pth

engine = create_engine(pth.SQLALCHEMY_DATABASE_URL)
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Any, Any, Any] | None:
    db = SessionFactory()

    try:
        yield db
    finally:
        db.close()
