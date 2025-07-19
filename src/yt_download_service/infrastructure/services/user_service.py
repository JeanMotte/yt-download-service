from uuid import UUID

from yt_download_service.infrastructure.database.models import DBUser
from yt_download_service.infrastructure.database.session import SessionFactory

from src.yt_download_service.app.interfaces.user_service import IUserService
from src.yt_download_service.domain.models.user import UserCreate, UserRead


class UserService(IUserService):
    """In-memory user service for demonstration purposes."""

    def __init__(self):
        # This will be implemented later
        self.users = []

    def create(self, user_to_create: UserCreate) -> UserRead:
        """Create a new user in the database."""
        db_user = DBUser(**user_to_create.model_dump())

        with SessionFactory() as db:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

        return UserRead.from_orm(db_user)

    def get_by_id(self, user_id: UUID) -> UserRead | None:
        """Get a user by their ID."""
        return next((user for user in self.users if user.id == user_id), None)

    def get_by_email(self, email: str) -> UserRead | None:
        """Get a user by their email."""
        return next((user for user in self.users if user.email == email), None)
