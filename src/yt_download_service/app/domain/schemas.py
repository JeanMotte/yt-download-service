from pydantic import BaseModel


class VideoURL(BaseModel):
    """Pydantic model for validating a YouTube video URL."""

    url: str


class Stream(BaseModel):
    """Pydantic model for representing a video stream."""

    url: str
    mime_type: str
    resolution: str
    video_codec: str
    audio_codec: str
