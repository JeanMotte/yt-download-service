from abc import ABC, abstractmethod
from uuid import UUID

from src.yt_download_service.domain.models.user import User


class IUserService(ABC):
    """Interface for user service."""

    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None:
        """Get a user by their ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Get a user by their email."""
        pass
