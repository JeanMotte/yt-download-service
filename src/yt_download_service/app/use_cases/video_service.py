from io import BytesIO
from typing import List

from pytube import YouTube
from yt_download_service.app.domain.schemas import Stream as StreamSchema
from yt_download_service.app.utils.video_utils import is_valid_youtube_url


class VideoService:
    """Service for downloading YouTube video segments."""

    def __init__(self) -> None:
        pass

    def get_video_formats(self, url: str) -> List[StreamSchema]:
        """Get all available video formats for a given YouTube video URL.

        Args:
        ----
            url: The URL of the YouTube video.

        Returns:
        -------
            A list of available video formats.

        """
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        yt = YouTube(url)
        formats = []
        for stream in yt.streams.filter(progressive=True):
            formats.append(
                StreamSchema(
                    url=stream.url,
                    mime_type=stream.mime_type,
                    resolution=stream.resolution,
                    video_codec=stream.video_codec,
                    audio_codec=stream.audio_codec,
                )
            )
        return formats

    def download_video(self, url: str) -> BytesIO:
        """Download a YouTube video in MP4 format.

        Args:
        ----
            url: The URL of the YouTube video.

        Returns:
        -------
            A file-like object containing the video data.

        """
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension="mp4").first()
        if not stream:
            raise ValueError("No MP4 stream available")

        buffer = BytesIO()
        stream.stream_to_buffer(buffer)
        buffer.seek(0)
        return buffer
