from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.yt_download_service.domain.models.history import (
    History,  # Use the Pydantic model
)


class IHistoryService(ABC):
    """Interface for history service, defining the contract for history operations."""

    @abstractmethod
    async def create_history_entry(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        video_url: str,
        video_title: str,
        format_id: str,
        resolution: str | None,
        start_time_str: str | None = None,
        end_time_str: str | None = None,
    ) -> None:
        """Contract for creating a new history record."""
        pass

    @abstractmethod
    async def get_history_by_user_id(
        self, db: AsyncSession, user_id: UUID
    ) -> list[History]:  # noqa: E501
        """Contract for getting history records by user ID."""
        pass
