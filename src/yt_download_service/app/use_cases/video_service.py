import asyncio
import datetime
import os
import re
import subprocess
import tempfile
from typing import Optional, Tuple, cast

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

    def _get_formats_sync(self, url: str) -> FormatsResponse:  # noqa: C901
        """Get video formats."""
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                formats = info_dict.get("formats", [])

                duration_in_seconds = info_dict.get("duration")
                if duration_in_seconds:
                    formatted_duration = str(
                        datetime.timedelta(seconds=int(duration_in_seconds))
                    )
                else:
                    formatted_duration = "00:00:00"
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
                    duration=formatted_duration,
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
        """Download a full video."""
        # 1. Get all video metadata without downloading.
        info_dict = self._get_video_info(url)
        video_title = info_dict.get("title", "Untitled")
        formats = info_dict.get("formats", [])
        video_duration_seconds = info_dict.get("duration")

        if video_duration_seconds is None:
            raise ValueError("Cannot determine video duration. Might be a live stream.")

        if video_duration_seconds > 120:  # Limit to 2 minutes
            raise ValueError("The video duration cannot exceed 2 minutes.")

        # 2. Find the direct URL for the requested video format.
        if format_id:
            video_format = next(
                (f for f in formats if f.get("format_id") == format_id), None
            )
            if not video_format:
                raise ValueError(f"Format ID {format_id} not found.")
        else:
            # If no format_id is provided, we must select the best one.
            video_only_formats = [
                f
                for f in formats
                if f.get("vcodec") != "none" and f.get("acodec") == "none"
            ]
            if not video_only_formats:
                raise ValueError("No suitable video-only format found for merging.")
            # Select the one with the greatest height (resolution).
            video_format = max(video_only_formats, key=lambda f: f.get("height", 0))

        video_url = video_format.get("url")
        resolution = video_format.get("resolution")
        final_format_id = video_format.get("format_id")  # Use the determined format_id

        # 3. Find the direct URL for the best audio format. (Same as optimal_sample)
        audio_streams = [
            f
            for f in formats
            if f.get("acodec") != "none" and f.get("vcodec") == "none"
        ]
        if not audio_streams:
            raise ValueError("No compatible audio stream found to merge.")

        def get_bitrate(fmt):
            abr = fmt.get("abr")
            return int(abr) if abr is not None else 0

        audio_streams.sort(key=lambda x: get_bitrate(x), reverse=True)
        best_audio_url = audio_streams[0].get("url")

        # 4. Construct the explicit ffmpeg command
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            output_path = temp_file.name

        ffmpeg_command = [
            "ffmpeg",
            "-loglevel",
            "error",
            "-i",
            video_url,
            "-i",
            best_audio_url,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-c:a",
            "aac",
            "-movflags",
            "frag_keyframe+empty_moov",
            "-f",
            "mp4",
            "pipe:1",
            "-y",  # Overwrite output file if it exists
            output_path,  # Direct output to our temporary file
        ]

        try:
            subprocess.run(ffmpeg_command, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # If ffmpeg fails, clean up the temp file before raising the error
            if os.path.exists(output_path):
                os.remove(output_path)
            error_message = (
                e.stderr.decode("utf-8") if e.stderr else "Unknown FFmpeg error"
            )
            raise ValueError(f"FFmpeg failed: {error_message}")

        # --- Return the path and metadata instead of a buffer ---
        return output_path, video_title, final_format_id, resolution

    # --- OPTIMAL VIDEO SAMPLE DOWNLOAD ---
    async def download_optimal_sample(
        self, url: str, start_time: str, end_time: str, format_id: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Async wrapper for the OPTIMAL video sample download."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._download_optimal_sample_sync_to_file,
            url,
            start_time,
            end_time,
            format_id,
        )

    def _download_optimal_sample_sync_to_file(
        self, url: str, start_time: str, end_time: str, format_id: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Download and trims video segment to a temporary file and returns the path."""
        info_dict = self._get_video_info(url)
        video_title = info_dict.get("title", "Unknown Title")
        formats = info_dict.get("formats", [])
        video_duration_seconds = info_dict.get("duration")

        start_seconds = self._time_str_to_seconds(start_time)
        end_seconds = self._time_str_to_seconds(end_time)
        duration = end_seconds - start_seconds

        if video_duration_seconds is None:
            raise ValueError("Cannot determine video duration. Might be a live stream.")
        if start_seconds < 0 or end_seconds > video_duration_seconds or duration <= 0:
            raise ValueError("Invalid start or end time.")
        if duration > 120:  # Limit sample duration to 2 minutes
            raise ValueError("The sample duration cannot exceed 2 minutes.")

        video_format = next(
            (f for f in formats if f.get("format_id") == format_id), None
        )
        if not video_format:
            raise ValueError(f"Format ID {format_id} not found for sample download.")
        video_url = video_format.get("url")
        resolution = video_format.get("resolution")

        audio_streams = [
            f
            for f in formats
            if f.get("acodec") != "none" and f.get("vcodec") == "none"
        ]
        if not audio_streams:
            raise ValueError("No compatible audio stream found to merge for sample.")

        def get_bitrate(fmt):
            abr = fmt.get("abr")
            return int(abr) if abr is not None else 0

        audio_streams.sort(key=lambda x: get_bitrate(x), reverse=True)
        best_audio_url = audio_streams[0].get("url")

        # Use a temporary file ---
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            output_path = temp_file.name

        ffmpeg_command = [
            "ffmpeg",
            "-loglevel",
            "error",
            "-ss",
            str(start_time),
            "-i",
            video_url,
            "-ss",
            str(start_time),
            "-i",
            best_audio_url,
            "-t",
            str(duration),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-c:a",
            "aac",
            "-movflags",
            "frag_keyframe+empty_moov",
            "-f",
            "mp4",
            "-y",  # Overwrite output file
            output_path,  # Direct output to our temporary file
        ]

        try:
            subprocess.run(ffmpeg_command, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            error_message = (
                e.stderr.decode("utf-8") if e.stderr else "Unknown FFmpeg error"
            )
            raise ValueError(f"FFmpeg failed for sample: {error_message}")

        # --- Return the path and metadata ---
        return output_path, video_title, format_id, resolution
