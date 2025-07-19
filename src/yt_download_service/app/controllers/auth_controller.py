from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse

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


@router.get("/auth/google")
async def auth_google(request: Request):
    """Call endpoint for Google authentication."""
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.parse_id_token(request, token)
    user = auth_service.authenticate_user(user_info)
    request.session["user"] = user.model_dump()
    return RedirectResponse(url="/")


@router.get("/me")
async def me(request: Request):
    """Return the current user."""
    user = request.session.get("user")
    if not user:
        return {"message": "Not authenticated"}
    return user
