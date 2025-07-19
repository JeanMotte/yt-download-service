from uuid import UUID

from src.yt_download_service.domain.models.commons.base_models import (
    TimedObjectModel,
    UUIdentifiedObjectModel,
)


class History(UUIdentifiedObjectModel, TimedObjectModel):
    """The history of downloaded videos."""

    user_id: UUID
    yt_video_id: str
    start_time: int
    end_time: int
