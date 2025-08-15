import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from yt_download_service.app.use_cases.auth_service import AuthService
from yt_download_service.app.utils.dependencies import (
    get_auth_service,
    get_current_user_from_token,
)
from yt_download_service.app.utils.google_sso import oauth
from yt_download_service.app.utils.jwt_handler import TokenResponse, create_access_token
from yt_download_service.domain.models.auth import GoogleToken
from yt_download_service.domain.models.user import UserRead
from yt_download_service.infrastructure.database.session import get_db_session

router = APIRouter()


@router.get("/login/google")
async def login_google(request: Request):
    """Redirect to Google for authentication."""
    redirect_uri = request.url_for("auth_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", response_model=TokenResponse)
async def auth_google(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Process Google callback, authenticate user, and return a JWT access token."""
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

    try:
        user: UserRead = await auth_service.authenticate_user(db, user_info)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Create a JWT for application
    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/google/token", response_model=TokenResponse)
async def login_google_token(
    google_token: GoogleToken,
    db: AsyncSession = Depends(get_db_session),
    # INJECT THE SERVICE: FastAPI will call get_auth_service() for you
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user using a Google access token obtained from the extension."""
    google_api_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {google_token.token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(google_api_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate Google token. Response: {response.text}",
        )

    user_info = response.json()
    if not user_info or not user_info.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve user info from Google.",
        )

    try:
        # The `auth_service` instance is fresh for this request and will work
        # correctly with the `db` session, which is also scoped to this request.
        user: UserRead = await auth_service.authenticate_user(db, user_info)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Create a JWT for your application
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def me(current_user: UserRead = Depends(get_current_user_from_token)):
    """Return the current authenticated user's details."""
    return current_user
