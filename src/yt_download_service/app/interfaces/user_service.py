from abc import ABC, abstractmethod
from uuid import UUID

from src.yt_download_service.domain.models.user import UserCreate, UserRead


class IUserService(ABC):
    """Interface for user service, defining the contract for user operations."""

    @abstractmethod
    def create(self, user_to_create: UserCreate) -> UserRead:
        """
        Create a new user.

        Accepts user creation data and returns the full user object from the DB.
        """
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> UserRead | None:
        """
        Get a user by their ID.

        Returns the full user object or None if not found.
        """
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> UserRead | None:
        """
        Get a user by their email.

        Returns the full user object or None if not found.
        """
        pass
