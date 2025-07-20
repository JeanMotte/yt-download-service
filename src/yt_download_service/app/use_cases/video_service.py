from io import BytesIO
from typing import List
from urllib.error import HTTPError

from fastapi.concurrency import run_in_threadpool
from pytube import YouTube
from yt_download_service.app.domain.schemas import Stream as StreamSchema
from yt_download_service.app.utils.video_utils import is_valid_youtube_url


# If you don't want to import from pytube.cli, you can define a simple dummy callback
def dummy_on_progress(stream, chunk, bytes_remaining):
    """Get Dummy progress callback function."""
    pass


class VideoService:
    """Service for downloading YouTube video segments."""

    def __init__(self) -> None:
        pass

    async def get_video_formats(self, url: str) -> List[StreamSchema]:
        """Get all available video formats for a given YouTube video URL."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        def _get_formats():
            try:
                # Add the on_progress_callback here
                print(f"[INFO] Initializing YouTube object for URL: {url}")
                yt = YouTube(url, on_progress_callback=dummy_on_progress)
                yt.check_availability()

                print("[INFO] Fetching progressive streams...")
                formats = [
                    StreamSchema(
                        url=stream.url,
                        mime_type=stream.mime_type,
                        resolution=stream.resolution,
                        video_codec=stream.video_codec,
                        audio_codec=stream.audio_codec,
                    )
                    for stream in yt.streams.filter(progressive=True)
                ]

                print(f"[INFO] Found {len(formats)} streams.")
                return formats
            except HTTPError as e:
                # A more user-friendly error message
                raise ValueError(
                    f"The video may be unavailable or private. (Original error: {e})"
                )
            except Exception as e:
                # Check for common pytube exceptions
                if "is age restricted" in str(e):
                    raise ValueError("Age-restricted video. Needs authentication.")
                import traceback

                traceback.print_exc()
                raise ValueError(f"An unexpected error occurred: {e}")

        return await run_in_threadpool(_get_formats)

    async def download_video(self, url: str) -> BytesIO:
        """Download a YouTube video in MP4 format."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        def _download():
            try:
                # Add the on_progress_callback here as well
                yt = YouTube(url, on_progress_callback=dummy_on_progress)
                yt.check_availability()
                stream = yt.streams.filter(
                    progressive=True, file_extension="mp4"
                ).first()
                if not stream:
                    raise ValueError(
                        "No progressive MP4 stream available for this video."
                    )

                buffer = BytesIO()
                stream.stream_to_buffer(buffer)
                buffer.seek(0)
                return buffer
            except HTTPError as e:
                raise ValueError(
                    f"The video may be unavailable or private. (Original error: {e})"
                )
            except Exception as e:
                if "is age restricted" in str(e):
                    raise ValueError("Age-restricted video. Needs authentication.")
                raise ValueError(f"An unexpected error occurred: {e}")

        return await run_in_threadpool(_download)
