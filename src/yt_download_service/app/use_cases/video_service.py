import asyncio
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

    async def download_video(
        self, url: str, format_id: Optional[str] = None
    ) -> BytesIO:
        """Download a YouTube video in MP4 format, optionally with a specific format."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_sync, url, format_id)

    def _download_sync(self, url: str, format_id: Optional[str] = None) -> BytesIO:
        """Download a video using yt-dlp."""
        try:
            buffer = BytesIO()

            # --- DYNAMIC FORMAT SELECTION ---
            # The formats you listed are video-only. To get a complete video,
            # you must combine a video stream with an audio stream.
            if format_id:
                # Combine the chosen video format with the best available audio
                format_selector = f"{format_id}+bestaudio[ext=m4a]/best"
            else:
                # Fallback to the best pre-merged format if no ID is given
                format_selector = (
                    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                )

            ydl_opts = {
                "format": format_selector,
                "outtmpl": "-",
                "logtostderr": True,
                "writetobuffer": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
                # This key is not always present with writetobuffer, use a safer way
                # The buffer is filled directly by the handler.
                # video_content = result["requested_downloads"][0]["buffer"].getvalue()
                # # This can fail
                # Instead, the buffer is managed within the context.
                # We just need to make sure
                # yt-dlp knows where to write. The hook system is better for this.

                # A more robust way to capture to buffer:
                # We'll write to our `buffer` object directly
                ydl.to_stdout = buffer
                ydl.download([url])

            buffer.seek(0)
            return buffer
        except yt_dlp.utils.DownloadError as e:
            # Provide a more helpful error message
            if "requested format not available" in str(e):
                raise ValueError(
                    f"Format ID '{format_id}' is not available for this video."
                )
            raise ValueError(f"Failed to download video: {e}")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred: {e}")
