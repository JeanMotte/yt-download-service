import asyncio
import os
import re
import subprocess
import tempfile
from io import BytesIO
from typing import Optional, cast

import yt_dlp
from yt_download_service.app.domain.schemas import (
    AudioOption,
    DownloadResult,
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

    def _get_video_info(self, url: str) -> dict:
        """Fetch video metadata without downloading."""
        ydl_opts = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return cast(dict, ydl.extract_info(url, download=False))

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
    ) -> DownloadResult:
        """Async wrapper for the download process."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._download_full_sync, url, format_id
        )

    def _download_full_sync(
        self, url: str, format_id: Optional[str] = None
    ) -> DownloadResult:
        """Download a video and returns it as a buffer along with its metadata."""
        # 1. Get metadata first
        info_dict = self._get_video_info(url)
        video_title = info_dict.get("title", "Unknown Title")

        # 2. Determine format and resolution
        if format_id:
            format_selector = f"{format_id}+bestaudio[ext=m4a]/{format_id}/best"
        else:
            format_selector = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        chosen_format = next(
            (
                f
                for f in info_dict.get("formats", [])
                if f.get("format_id") == format_id
            ),
            None,
        )
        resolution = chosen_format.get("resolution") if chosen_format else None

        # 3. Download the video
        with tempfile.TemporaryDirectory() as temp_dir:
            output_template = os.path.join(temp_dir, "video.%(ext)s")
            ydl_opts = {
                "format": format_selector,
                "merge_output_format": "mp4",
                "outtmpl": output_template,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # The info dict from download has the final format info
                final_info = ydl.extract_info(url, download=True)
                downloaded_filepath = ydl.prepare_filename(final_info)
                final_format_id = final_info.get("format_id")

                # If resolution wasn't found before, try again with final info
                if not resolution:
                    resolution = final_info.get("resolution")

            if not os.path.exists(downloaded_filepath):
                raise ValueError("Download failed, file not found.")

            buffer = BytesIO()
            with open(downloaded_filepath, "rb") as f:
                buffer.write(f.read())
            buffer.seek(0)

            return DownloadResult(
                file_buffer=buffer,
                video_title=video_title,
                resolution=resolution,
                final_format_id=final_format_id,
            )

    # --- VIDEO SAMPLE DOWNLOAD ---
    async def download_video_sample(
        self, url: str, start_time: str, end_time: str, format_id: Optional[str] = None
    ) -> DownloadResult:
        """Async wrapper for downloading a video sample."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._download_sample_sync, url, start_time, end_time, format_id
        )

    def _download_sample_sync(
        self, url: str, start_time: str, end_time: str, format_id: Optional[str] = None
    ) -> DownloadResult:
        """Download and clips a video, returning the sample buffer and metadata."""
        # 1. Get metadata
        info_dict = self._get_video_info(url)
        video_title = info_dict.get("title", "Unknown Title")

        # 2. Perform the download and cut (re-using your existing logic)
        full_download_result = self._download_full_sync(url, format_id)

        # 3. Cut the sample from the full video buffer
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
            temp_input.write(full_download_result.file_buffer.read())
            temp_input_path = temp_input.name

        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp4") as temp_output:
            sample_output_path = temp_output.name

            ffmpeg_command = [
                "ffmpeg",
                "-y",
                "-i",
                temp_input_path,
                "-ss",
                start_time,
                "-to",
                end_time,
                "-c",
                "copy",
                sample_output_path,
            ]
            subprocess.run(ffmpeg_command, check=True, capture_output=True)

            buffer = BytesIO()
            with open(sample_output_path, "rb") as f:
                buffer.write(f.read())
            buffer.seek(0)

        os.remove(temp_input_path)  # Clean up temp input file

        # 4. Return the result
        return DownloadResult(
            file_buffer=buffer,
            video_title=video_title,
            resolution=full_download_result.resolution,
            final_format_id=full_download_result.final_format_id,
        )

    async def download_optimal_sample(
        self, url: str, start_time: str, end_time: str, format_id: Optional[str] = None
    ) -> DownloadResult:
        """Async wrapper for the OPTIMAL video sample download."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._download_optimal_sample_sync,
            url,
            start_time,
            end_time,
            format_id,
        )

    def _download_optimal_sample_sync(
        self, url: str, start_time: str, end_time: str, format_id: Optional[str] = None
    ) -> DownloadResult:
        """Download only the video segment using ffmpeg's seeking capabilities."""
        # 1. Get metadata first to have the title available.
        info_dict = self._get_video_info(url)
        video_title = info_dict.get("title", "Unknown Title")

        # 2. Determine format selector.
        if format_id:
            format_selector = f"{format_id}+bestaudio[ext=m4a]/{format_id}/best"
        else:
            format_selector = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

        # 3. Set up yt-dlp options for an optimal download.
        with tempfile.TemporaryDirectory() as temp_dir:
            output_template = os.path.join(temp_dir, "video-sample.%(ext)s")

            ffmpeg_args = {
                "ffmpeg_i": [
                    "-ss",
                    start_time,
                    "-to",
                    end_time,
                ]
            }

            ydl_opts = {
                "format": format_selector,
                "merge_output_format": "mp4",
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
                # Use ffmpeg for downloading these streams, and pass our arguments to it
                "external_downloader": "ffmpeg",
                "external_downloader_args": ffmpeg_args,
            }

            # 4. Execute the download.
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                final_info = ydl.extract_info(url, download=True)
                downloaded_filepath = ydl.prepare_filename(final_info)
                final_format_id = final_info.get("format_id")
                resolution = final_info.get("resolution")

            if not os.path.exists(downloaded_filepath):
                raise ValueError("Optimal sample download failed, file not found.")

            # 5. Read the downloaded sample into a buffer.
            buffer = BytesIO()
            with open(downloaded_filepath, "rb") as f:
                buffer.write(f.read())
            buffer.seek(0)

            # 6. Return the result.
            return DownloadResult(
                file_buffer=buffer,
                video_title=video_title,
                resolution=resolution,
                final_format_id=final_format_id,
            )
