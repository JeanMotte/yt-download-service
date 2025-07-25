from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.yt_download_service.domain.models.user import UserCreate, UserRead


class IUserService(ABC):
    """Interface for user service, defining the contract for user operations."""

    @abstractmethod
    async def create(self, db: AsyncSession, user_to_create: UserCreate) -> UserRead:
        """Create a new user."""
        pass

    @abstractmethod
    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> UserRead | None:
        """Get a user by their ID."""
        pass

    @abstractmethod
    async def get_by_email(self, db: AsyncSession, email: str) -> UserRead | None:
        """Get a user by their email."""
        pass
