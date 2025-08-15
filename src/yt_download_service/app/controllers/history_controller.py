from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from yt_download_service.app.use_cases.history_service import HistoryService
from yt_download_service.app.utils.dependencies import (
    get_current_user_from_token,
    get_db_session,
)
from yt_download_service.domain.models.history import History
from yt_download_service.domain.models.user import UserRead

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


@router.delete(
    "/",
    summary="Clear User Download History",
    description="Clears the download history for the currently authenticated user.",
)
async def clear_user_history(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user_from_token),
):
    """
    Clear the history for the logged-in user.

    The user ID is taken from the authentication token, ensuring users
    can only clear their own history.
    """
    deleted_count = await history_service.clear_history_by_user_id(
        db, user_id=current_user.id
    )
    return {
        "message": "Successfully cleared user download history.",
        "deleted_count": deleted_count,
    }


@router.delete(
    "/{history_id}",
    summary="Delete Specific Download History Entry",
    description="Deletes a specific download history entry for the currently authenticated user.",  # noqa: E501
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_history_entry(
    history_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user_from_token),
):
    """
    Delete a specific history entry for the logged-in user.

    The user ID is taken from the authentication token, ensuring users
    can only delete their own history entries.
    """
    await history_service.delete_history_by_id(
        db, history_id=history_id, user_id=current_user.id
    )
    return None
