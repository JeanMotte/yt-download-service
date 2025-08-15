from uuid import UUID

from pydantic import ConfigDict
from yt_download_service.domain.models.commons.base_models import (
    TimedObjectModel,
    UUIdentifiedObjectModel,
)


class History(UUIdentifiedObjectModel, TimedObjectModel):
    """The history of downloaded videos."""

    user_id: UUID
    yt_video_url: str
    video_title: str
    resolution: str | None  # Nullable for audio-only
    format_id: str  # Format ID of the downloaded video
    start_time: int | None  # Nullable for full video
    end_time: int | None  # Nullable for full video

    # Ok to create the model from object attributes
    model_config = ConfigDict(from_attributes=True)
