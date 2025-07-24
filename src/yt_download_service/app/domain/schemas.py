from typing import Annotated, List, Optional

from pydantic import BaseModel, Field


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


class DownloadSampleRequest(DownloadRequest):
    """Schema for downloading a video sample."""

    start_time: Annotated[
        str, Field(description="Start time in HH:MM:SS", examples=["00:01:10"])
    ]
    end_time: Annotated[
        str, Field(description="End time in HH:MM:SS", examples=["00:01:25"])
    ]


# Formats models
class ResolutionOption(BaseModel):
    """Model for a video resolution option."""

    resolution: str
    format_id: str
    has_audio: bool
    note: Optional[str] = None


class AudioOption(BaseModel):
    """Model for an audio format option."""

    format_id: str
    note: Optional[str] = None


class FormatsResponse(BaseModel):
    """Response model for available video formats."""

    title: str
    thumbnail_url: Optional[str] = None
    resolutions: List[ResolutionOption]
    audio_only: List[AudioOption]
