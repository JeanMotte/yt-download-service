from src.yt_download_service.app.interfaces.user_service import IUserService
from src.yt_download_service.domain.models.user import User


class AuthService:
    """Service for user authentication."""

    def __init__(self, user_service: IUserService):
        self.user_service = user_service

    def authenticate_user(self, user_info: dict) -> User:
        """Authenticate a user."""
        user = self.user_service.get_by_email(user_info["email"])
        if user:
            return user

        user = User(
            first_name=user_info["given_name"],
            last_name=user_info["family_name"],
            email=user_info["email"],
        )
        return self.user_service.create(user)
