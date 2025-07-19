from uuid import UUID

from src.yt_download_service.app.interfaces.user_service import IUserService
from src.yt_download_service.domain.models.user import User


class UserService(IUserService):
    """In-memory user service for demonstration purposes."""

    def __init__(self):
        # This will be implemented later
        self.users = []

    def create(self, user: User) -> User:
        """Create a new user."""
        self.users.append(user)
        return user

    def get_by_id(self, user_id: UUID) -> User | None:
        """Get a user by their ID."""
        return next((user for user in self.users if user.id == user_id), None)

    def get_by_email(self, email: str) -> User | None:
        """Get a user by their email."""
        return next((user for user in self.users if user.email == email), None)
