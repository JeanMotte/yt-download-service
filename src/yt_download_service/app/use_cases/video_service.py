import asyncio
import os
import tempfile
from io import BytesIO
from typing import List, Optional

import yt_dlp
from yt_download_service.app.domain.schemas import Stream as StreamSchema
from yt_download_service.app.utils.video_utils import is_valid_youtube_url


class VideoService:
    """Service for downloading YouTube video segments."""

    def __init__(self) -> None:
        pass

    async def get_video_formats(self, url: str) -> List[StreamSchema]:
        """Get all available video formats for a given YouTube video URL."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_formats_sync, url)

    def _get_formats_sync(self, url: str) -> List[StreamSchema]:
        """Get video formats using yt-dlp."""
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "noplaylist": True,
                "extract_flat": False,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                formats = info_dict.get("formats", [])

                streams = [
                    StreamSchema(
                        format_id=f.get("format_id"),
                        url=f.get("url"),
                        mime_type=f.get("mime_type"),
                        resolution=f.get("resolution"),
                        video_codec=f.get("vcodec"),
                        audio_codec=f.get("acodec"),
                    )
                    for f in formats
                    if f.get("vcodec") != "none"
                ]
                print(streams)
                return streams
        except yt_dlp.utils.DownloadError as e:
            raise ValueError(f"Failed to fetch video formats: {e}")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred: {e}")

    async def download_full_video(
        self, url: str, format_id: Optional[str] = None
    ) -> BytesIO:
        """Download a YouTube video in MP4 format, optionally with a specific format."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_sync, url, format_id)

    def _download_sync(self, url: str, format_id: Optional[str] = None) -> BytesIO:
        """
        Download a video using yt-dlp by saving it to a temporary file.

        And then loading it into memory.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                if format_id:
                    format_selector = f"{format_id}+bestaudio[ext=m4a]/{format_id}/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"  # noqa: E501
                else:
                    format_selector = (
                        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                    )

                # Define the output path template
                output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

                ydl_opts = {
                    "format": format_selector,
                    "merge_output_format": "mp4",
                    "outtmpl": output_template,
                    "logtostderr": True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # First, extract info without downloading to get the final filename
                    # This is a more robust way to predict the output filename
                    info_dict = ydl.extract_info(url, download=False)
                    downloaded_filepath = ydl.prepare_filename(info_dict)

                    # Actual download
                    ydl.download([url])

                if not os.path.exists(downloaded_filepath):
                    print(f"DEBUG: Expected file path not found: {downloaded_filepath}")
                    print(f"DEBUG: Contents of temp dir: {os.listdir(temp_dir)}")
                    raise ValueError(
                        "yt-dlp downloaded a file, but final path could not be found."
                    )

                buffer = BytesIO()
                with open(downloaded_filepath, "rb") as f:
                    buffer.write(f.read())

                buffer.seek(0)
                return buffer

            except yt_dlp.utils.DownloadError as e:
                if "Requested format is not available" in str(e):
                    raise ValueError(
                        f"Format ID '{format_id}' could not be used for downloading."
                    )
                raise ValueError(f"Failed to download video: {e}")
            except Exception as e:
                # Add more detailed logging here for easier debugging
                print(f"An unexpected error occurred: {type(e).__name__} - {e}")
                import traceback

                traceback.print_exc()
                raise ValueError(
                    "An unexpected error occurred in the download process."
                )
