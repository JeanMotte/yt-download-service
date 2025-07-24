import asyncio
import os
import re
import subprocess
import tempfile
from io import BytesIO
from typing import Optional

import yt_dlp
from yt_download_service.app.domain.schemas import (
    AudioOption,
    FormatsResponse,
    ResolutionOption,
)
from yt_download_service.app.utils.video_utils import is_valid_youtube_url


class VideoService:
    """Service for downloading YouTube video segments."""

    def __init__(self) -> None:
        pass

    def _time_str_to_seconds(self, time_str: str) -> int:
        """Convert HH:MM:SS string to seconds."""
        if not re.match(r"^\d{1,2}:\d{2}:\d{2}$", time_str):
            raise ValueError("Invalid time format. Please use HH:MM:SS.")
        parts = list(map(int, time_str.split(":")))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        # Handle MM:SS if needed, though we enforce HH:MM:SS
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return 0

    # ---FORMATS---

    async def get_video_formats(self, url: str) -> FormatsResponse:
        """Get video formats using yt-dlp."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_formats_sync, url)

    def _get_formats_sync(self, url: str) -> FormatsResponse:
        """Get video formats."""
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                formats = info_dict.get("formats", [])

                # 1. Check if there's any audio stream available at all
                has_any_audio = any(f.get("acodec") != "none" for f in formats)

                # 2. Group video streams by resolution, preferring mp4 (avc1)
                processed_resolutions: dict[str, dict[str, object]] = {}
                for f in formats:
                    # Video-only streams to avoid duplicates
                    if f.get("vcodec") == "none" or f.get("acodec") != "none":
                        continue

                    height = f.get("height")
                    if not height:
                        continue

                    resolution_key = f"{height}p"

                    is_mp4 = f.get("vcodec", "").startswith("avc")

                    if resolution_key not in processed_resolutions or (
                        is_mp4
                        and not processed_resolutions[resolution_key].get(
                            "is_mp4", False
                        )
                    ):
                        processed_resolutions[resolution_key] = {
                            "height": height,
                            "format_id": f.get("format_id"),
                            "is_mp4": is_mp4,
                        }

                # 3. Convert the dictionary to a sorted list of ResolutionOption
                resolution_options = [
                    ResolutionOption(
                        resolution=f"{data['height']}p",
                        format_id=data["format_id"],
                        has_audio=has_any_audio,
                    )
                    for res, data in processed_resolutions.items()
                ]
                # Sort from highest resolution to lowest
                resolution_options.sort(
                    key=lambda x: int(x.resolution[:-1]), reverse=True
                )

                if resolution_options:
                    resolution_options[0].note = "Best quality"

                # 4. Find the best audio-only stream (m4a is usually best for merging)
                audio_streams = [
                    f
                    for f in formats
                    if f.get("acodec") != "none" and f.get("vcodec") == "none"
                ]  # noqa: E501
                best_audio = None
                if audio_streams:
                    # --- START FIX ---
                    def get_bitrate(fmt):
                        abr = fmt.get("abr")
                        return int(abr) if abr is not None else 0

                    # Prefer m4a (AAC) audio, then sort by bitrate
                    audio_streams.sort(
                        key=lambda x: (x.get("ext") == "m4a", get_bitrate(x)),
                        reverse=True,
                    )
                    best_audio_format = audio_streams[0]

                    # Use the safe bitrate value for the note
                    bitrate = get_bitrate(best_audio_format)
                    note_text = f"{best_audio_format.get('ext')}, ~{bitrate}kbps"

                    best_audio = AudioOption(
                        format_id=best_audio_format.get("format_id"),
                        note=note_text,
                    )

                return FormatsResponse(
                    title=info_dict.get("title", "Untitled"),
                    thumbnail_url=info_dict.get("thumbnail"),
                    resolutions=resolution_options,
                    audio_only=[best_audio] if best_audio else [],
                )

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
        return await loop.run_in_executor(
            None, self._download_full_sync, url, format_id
        )

    def _download_full_sync(self, url: str, format_id: Optional[str] = None) -> BytesIO:
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

    # --- VIDEO SAMPLE DOWNLOAD ---
    async def download_video_sample(
        self,
        url: str,
        start_time: str,
        end_time: str,
        format_id: Optional[str] = None,
    ) -> BytesIO:
        """Download a sample of a YouTube video."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._download_sample_sync, url, start_time, end_time, format_id
        )

    def _download_sample_sync(
        self, url: str, start_time: str, end_time: str, format_id: Optional[str] = None
    ) -> BytesIO:
        """
        Download a full video and then uses ffmpeg to cut a sample.

        This is more reliable but less efficient than using download_ranges.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # --- Step 1: Download the full video (like in _download_full_sync) ---
                if format_id:
                    format_selector = f"{format_id}+bestaudio[ext=m4a]/{format_id}/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"  # noqa: E501
                else:
                    format_selector = (
                        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                    )

                full_video_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

                ydl_opts_download = {
                    "format": format_selector,
                    "merge_output_format": "mp4",
                    "outtmpl": full_video_template,
                    "logtostderr": True,
                }

                with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    full_video_path = ydl.prepare_filename(info_dict)
                    ydl.download([url])

                if not os.path.exists(full_video_path):
                    raise ValueError("Failed to download the full video for clipping.")

                # --- Step 2: Cut the downloaded video with FFmpeg ---
                sample_output_path = os.path.join(temp_dir, "video_sample.mp4")

                # -c avoids re-encoding, making the cut almost instantaneous.
                ffmpeg_command = [
                    "ffmpeg",
                    "-i",
                    full_video_path,  # Input file
                    "-ss",
                    start_time,  # Start time (e.g., "00:01:00")
                    "-to",
                    end_time,  # End time (e.g., "00:01:30")
                    "-c",
                    "copy",  # Copy codecs without re-encoding
                    sample_output_path,  # Output file
                ]

                # Execute the command
                subprocess.run(
                    ffmpeg_command, check=True, capture_output=True, text=True
                )

                # --- Step 3: Read the cut sample into a buffer ---
                buffer = BytesIO()
                with open(sample_output_path, "rb") as f:
                    buffer.write(f.read())

                buffer.seek(0)
                return buffer

            except subprocess.CalledProcessError as e:
                # Log ffmpeg errors for debugging
                print("FFMPEG Error:", e.stderr)
                raise ValueError("Failed to cut the video sample using ffmpeg.")
            except Exception as e:
                import traceback

                traceback.print_exc()
                raise ValueError(
                    f"An unexpected error occurred during sample creation: {e}"
                )
