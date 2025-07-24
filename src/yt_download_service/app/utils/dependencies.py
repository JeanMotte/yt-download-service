from fastapi import HTTPException, Request, status
from pydantic import ValidationError
from yt_download_service.domain.models.user import UserRead


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
        # This can happen if the UserRead model changes but the session data is old
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user session data",
        )
