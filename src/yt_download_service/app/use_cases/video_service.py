import asyncio
from io import BytesIO
from typing import List

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

    async def download_video(self, url: str) -> BytesIO:
        """Download a YouTube video in MP4 format."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_sync, url)

    def _download_sync(self, url: str) -> BytesIO:
        """Download a video using yt-dlp."""
        try:
            buffer = BytesIO()
            ydl_opts = {
                # Format 'best' will get the best video and best audio and merge them
                # 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]' is more robust.
                "format": "best[ext=mp4]",
                "outtmpl": "-",  # Special value for "to buffer"
                "logtostderr": True,
                "writetobuffer": True,  # Tell yt-dlp to write to the buffer
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # ydl.download() is more direct for just downloading
                result = ydl.extract_info(url, download=True)
                # The content is written to stdout, and captured by `writetobuffer`
                video_content = result["requested_downloads"][0]["buffer"].getvalue()

            buffer.write(video_content)
            buffer.seek(0)
            return buffer
        except yt_dlp.utils.DownloadError as e:
            raise ValueError(f"Failed to download video: {e}")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred: {e}")
