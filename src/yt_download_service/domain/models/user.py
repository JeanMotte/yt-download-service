from src.yt_download_service.domain.models.commons.base_models import (
    TimedObjectModel,
    UUIdentifiedObjectModel,
)


class User(UUIdentifiedObjectModel, TimedObjectModel):
    """The user of the app."""

    first_name: str
    last_name: str
    email: str
