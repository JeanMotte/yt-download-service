from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.yt_download_service.app.use_cases.history_service import HistoryService
from src.yt_download_service.app.utils.dependencies import (
    get_current_user_from_token,
    get_db_session,
)
from src.yt_download_service.domain.models.history import History
from src.yt_download_service.domain.models.user import UserRead

router = APIRouter()
history_service = HistoryService()


@router.get(
    "/",
    response_model=list[History],
    summary="Get User Download History",
    description="Retrieves the download history for the currently authenticated user.",
)
async def get_user_history(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user_from_token),
):
    """
    Get the history for the logged-in user.

    The user ID is taken from the authentication token, ensuring users
    can only access their own history.
    """
    history_records = await history_service.get_history_by_user_id(
        db, user_id=current_user.id
    )
    return history_records
