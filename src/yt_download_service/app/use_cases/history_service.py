from typing import cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from yt_download_service.domain.models.history import History
from yt_download_service.infrastructure.database.models import DBHistory


class HistoryService:
    """Service for managing user download history."""

    def _time_str_to_seconds(self, time_str: str | None) -> int | None:
        """Convert HH:MM:SS string to seconds. Returns None if input is None."""
        if time_str is None:
            return None
        parts = list(map(int, time_str.split(":")))
        return parts[0] * 3600 + parts[1] * 60 + parts[2]

    async def create_history_entry(
        self,
        db: AsyncSession,
        *,  # Make all subsequent arguments keyword-only for clarity
        user_id: UUID,
        video_url: str,
        video_title: str,
        format_id: str,
        resolution: str | None,
        start_time_str: str | None = None,
        end_time_str: str | None = None,
    ) -> None:
        """
        Create and save a new history entry in the database.

        Designed to be run in the background.
        """
        try:
            history_entry = DBHistory(
                user_id=user_id,
                yt_video_url=video_url,
                video_title=video_title,
                format_id=format_id,
                resolution=resolution,
                start_time=self._time_str_to_seconds(start_time_str),
                end_time=self._time_str_to_seconds(end_time_str),
            )
            db.add(history_entry)
            await db.commit()
            print(
                f"Successfully saved history for user {user_id} and video '{video_title}'."  # noqa: E501
            )
        except Exception as e:
            # In a real app, you'd use a proper logger
            print(f"Error saving history to DB: {e}")
            await db.rollback()

    async def get_history_by_user_id(
        self, db: AsyncSession, user_id: UUID
    ) -> list[History]:
        """Retrieve all history entries for a given user ID, ordered by most recent."""
        try:
            query = (
                select(DBHistory)
                .where(DBHistory.user_id == user_id)
                .order_by(desc(DBHistory.created_at))
            )
            result = await db.execute(query)
            db_histories = result.scalars().all()

            # Map the DB objects to Pydantic models before returning
            return [History.model_validate(db_obj) for db_obj in db_histories]

        except Exception as e:
            print(f"Error retrieving history for user {user_id}: {e}")
            return []

    async def delete_history_by_id(
        self, db: AsyncSession, *, history_id: UUID, user_id: UUID
    ) -> None:
        """
        Delete a specific history entry for a given user.

        Raises HTTPException if the entry is not found or doesn't belong to the user.
        """
        # 1. Fetch the entry and verify ownership in one query
        query = select(DBHistory).where(
            DBHistory.id == history_id, DBHistory.user_id == user_id
        )
        result = await db.execute(query)
        db_history = result.scalar_one_or_none()

        # 2. Handle not found case
        if not db_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"History entry with id {history_id} not found for this user.",
            )

        # 3. Delete and commit
        try:
            await db.delete(db_history)
            await db.commit()
            print(
                f"Successfully deleted history entry {history_id} for user {user_id}."
            )
        except Exception as e:
            await db.rollback()
            print(f"Error deleting history entry {history_id}: {e}")
            # Re-raise as a server error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not delete history entry.",
            )

    async def clear_history_by_user_id(self, db: AsyncSession, user_id: UUID) -> int:
        """
        Clear all history entries for a given user ID using a single bulk delete.

        Returns the number of deleted rows.
        """
        try:
            # 1. Create a single bulk delete statement
            query = delete(DBHistory).where(DBHistory.user_id == user_id)

            # 2. Execute it
            result = await db.execute(query)
            await db.commit()

            deleted_count = result.rowcount
            print(
                f"Successfully cleared {deleted_count} history entries for user {user_id}."  # noqa: E501
            )
            return cast(int, deleted_count)

        except Exception as e:
            await db.rollback()
            print(f"Error clearing history for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not clear user history.",
            )
