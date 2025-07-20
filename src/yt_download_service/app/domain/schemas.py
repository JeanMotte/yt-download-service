from typing import Optional

from pydantic import BaseModel


class VideoURL(BaseModel):
    """Pydantic model for validating a YouTube video URL."""

    url: str


class Stream(BaseModel):
    """Pydantic model for representing a video stream."""

    format_id: str
    url: str
    mime_type: Optional[str] = None
    resolution: str
    video_codec: str
    audio_codec: str


class DownloadRequest(BaseModel):
    """Pydantic model for a download request."""

    url: str
    format_id: Optional[str] = None
