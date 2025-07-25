from sqlalchemy.ext.asyncio import AsyncSession

from src.yt_download_service.app.interfaces.user_service import IUserService
from src.yt_download_service.domain.models.user import UserCreate, UserRead


class AuthService:
    """Service for user authentication."""

    def __init__(self, user_service: IUserService):
        self.user_service = user_service

    async def authenticate_user(self, db: AsyncSession, user_info: dict) -> UserRead:
        """Authenticate user by finding them by email. Creating them if don't exist."""
        email = user_info.get("email")
        if not email:
            raise ValueError("User info from provider is missing an email address.")

        # 2. Use AWAIT and pass the DB session to the user service
        user = await self.user_service.get_by_email(db, email=email)
        if user:
            return user

        # User does not exist, so create a new one
        user_to_create = UserCreate(
            first_name=user_info.get("given_name", ""),
            last_name=user_info.get("family_name", ""),
            email=email,
        )

        # 3. Use AWAIT and pass the DB session here as well
        new_user = await self.user_service.create(db, user_to_create=user_to_create)
        return new_user
