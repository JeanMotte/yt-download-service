"""Database models for the application."""

from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

Base: Any = declarative_base()


class DBUser(Base):
    """Database model for a user."""

    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    history: Mapped[list["DBHistory"]] = relationship(
        "DBHistory", back_populates="user"
    )


class DBHistory(Base):
    """Database model for a history entry."""

    __tablename__ = "history"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    yt_video_url: Mapped[str] = mapped_column(String, nullable=False)
    video_title: Mapped[str] = mapped_column(String, nullable=False)
    resolution: Mapped[str | None] = mapped_column(String, nullable=True)
    format_id: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[int] = mapped_column(Integer, nullable=True)
    end_time: Mapped[int] = mapped_column(Integer, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["DBUser"] = relationship("DBUser", back_populates="history")
