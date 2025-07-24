from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError
from yt_download_service.app.utils.jwt_handler import decode_access_token
from yt_download_service.domain.models.user import UserRead

from src.yt_download_service.infrastructure.services.user_service import UserService


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


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/google")
user_service = UserService()


async def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> UserRead:
    """
    Get the current user from a JWT token.

    1. Decodes the JWT from the Authorization header.
    2. Extracts the user's email (or ID).
    3. Fetches the user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        email: str | None = payload.get(
            "sub"
        )  # 'sub' is the standard claim for subject (user)
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = user_service.get_by_email(email)
    if user is None:
        raise credentials_exception

    return user
