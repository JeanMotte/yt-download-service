from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from yt_download_service.app.interfaces.user_service import IUserService
from yt_download_service.app.use_cases.auth_service import AuthService
from yt_download_service.app.utils.jwt_handler import decode_access_token
from yt_download_service.domain.models.user import UserRead
from yt_download_service.infrastructure.database.session import get_db_session
from yt_download_service.infrastructure.services.user_service import UserService


async def get_current_user(request: Request) -> UserRead:
    """
    Dependency function to get the current user from the session.

    Raises HTTPException 401 if the user is not authenticated.
    """
    user_dict = request.session.get("user")
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # Validate the dictionary from the session is a valid UserRead model
        return UserRead.model_validate(user_dict)
    except ValidationError:
        # If the UserRead model changes but the session data is old
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user session data",
        )


security_scheme = HTTPBearer(auto_error=False)
user_service = UserService()


async def get_current_user_from_token(
    auth_credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> UserRead:
    """Get the current user from a JWT token in the Authorization header."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Check if the header was provided and is of type Bearer
    if auth_credentials is None or auth_credentials.scheme != "Bearer":
        raise credentials_exception

    # 2. The token is in the `credentials` attribute
    token = auth_credentials.credentials

    try:
        payload = decode_access_token(token)
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        # This catches invalid signature, expired token, etc.
        raise credentials_exception

    user = await user_service.get_by_email(db, email=email)
    if user is None:
        # This catches the case where the user from a valid token was deleted
        raise credentials_exception

    return user


def get_user_service() -> UserService:
    """Dependency provider for UserService."""
    return UserService()


def get_auth_service(
    # FastAPI sees this and knows it must first run the `get_user_service`
    # dependency and pass its result into this `user_service` argument.
    user_service: IUserService = Depends(get_user_service),
) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(user_service=user_service)
