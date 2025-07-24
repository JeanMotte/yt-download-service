from fastapi import APIRouter, HTTPException, Request, status
from fastapi.params import Depends
from yt_download_service.app.utils.dependencies import get_current_user_from_token
from yt_download_service.app.utils.jwt_handler import TokenResponse, create_access_token
from yt_download_service.domain.models.user import UserRead

from src.yt_download_service.app.use_cases.auth_service import AuthService
from src.yt_download_service.app.utils.google_sso import oauth
from src.yt_download_service.infrastructure.services.user_service import UserService

router = APIRouter()

user_service = UserService()
auth_service = AuthService(user_service)


@router.get("/login/google")
async def login_google(request: Request):
    """Redirect to Google for authentication."""
    redirect_uri = request.url_for("auth_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", response_model=TokenResponse)
async def auth_google(request: Request):
    """
    Process Google callback, authenticate user, and return a JWT access token.

    This is now an API endpoint, not a redirector.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not authorize with Google: {e}",
        )

    user_info = token.get("userinfo")
    if not user_info or not user_info.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve user info from Google.",
        )

    # Use the existing service to find or create the user
    user: UserRead = auth_service.authenticate_user(user_info)

    # Create a JWT for our application
    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def me(current_user: UserRead = Depends(get_current_user_from_token)):
    """Return the current authenticated user's details."""
    return current_user
