from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
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
