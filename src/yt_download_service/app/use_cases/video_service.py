import asyncio
import base64
import datetime
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from typing import Generator, Optional, Tuple, cast

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

    @contextmanager
    def _get_cookie_file_path(
        self, encoded_cookies: str | None
    ) -> Generator[str | None, None, None]:
        """Decode cookies."""
        """Decodes base64 cookies, writes them to a temporary
        file, yields the file path, and securely cleans up afterwards.
        """
        if not encoded_cookies:
            yield None
            return

        cookie_file_path = None
        try:
            # Decode the Base64 string back to the original text content
            decoded_cookies = base64.b64decode(encoded_cookies).decode("utf-8")

            # Create a temporary file that is deleted on close
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".txt", encoding="utf-8"
            ) as temp_cookie_file:
                temp_cookie_file.write(decoded_cookies)
                cookie_file_path = temp_cookie_file.name

            yield cookie_file_path  # The path is used by the 'with' block

        finally:
            # Securely clean up the file after the 'with' block is exited
            if cookie_file_path and os.path.exists(cookie_file_path):
                os.remove(cookie_file_path)

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

    def _get_video_info(self, url: str, encoded_cookies: str | None = None) -> dict:
        """Fetch video metadata without downloading."""
        with self._get_cookie_file_path(encoded_cookies) as cookie_path:
            ydl_opts = {"quiet": True, "no_warnings": True}
            if cookie_path:
                ydl_opts["cookiefile"] = cookie_path

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return cast(dict, ydl.extract_info(url, download=False))

    # ---FORMATS---

    async def get_video_formats(
        self, url: str, encoded_cookies: str | None = None
    ) -> FormatsResponse:
        """Get video formats using yt-dlp."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_formats_sync, url)

    def _get_formats_sync(  # noqa: C901
        self, url: str, encoded_cookies: str | None = None
    ) -> FormatsResponse:  # noqa: C901
        """Get video formats."""
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts):
                info_dict = self._get_video_info(url, encoded_cookies=encoded_cookies)
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
                    if f.get("protocol") in ("m3u8", "m3u8_native"):
                        continue
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
        self,
        url: str,
        format_id: Optional[str] = None,
        encoded_cookies: str | None = None,
    ) -> DownloadResult:
        """Async wrapper for the download process."""
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._download_full_sync, url, format_id, encoded_cookies
        )

    def _download_full_sync(
        self,
        url: str,
        format_id: Optional[str] = None,
        encoded_cookies: str | None = None,
    ) -> DownloadResult:
        """Download a full video."""
        # 1. Get all video metadata without downloading.
        info_dict = self._get_video_info(url, encoded_cookies=encoded_cookies)
        video_title = info_dict.get("title", "Untitled")
        formats = info_dict.get("formats", [])
        video_duration_seconds = info_dict.get("duration")

        if video_duration_seconds is None:
            raise ValueError("Cannot determine video duration. Might be a live stream.")

        if video_duration_seconds > 180:  # Limit to 3 minutes
            raise ValueError("The video duration cannot exceed 3 minutes.")

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
        self,
        url: str,
        start_time: str,
        end_time: str,
        format_id: Optional[str] = None,
        encoded_cookies: str | None = None,
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
            encoded_cookies,
        )

    def _download_optimal_sample_sync_to_file(  # noqa: C901
        self,
        url: str,
        start_time: str,
        end_time: str,
        video_format_id: Optional[str] = None,
        encoded_cookies: str | None = None,
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Download and trims video segment to a temporary file."""
        info_dict = self._get_video_info(url, encoded_cookies=encoded_cookies)
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
        if duration > 180:  # Limit sample duration to 3 minutes
            raise ValueError("The sample duration cannot exceed 3 minutes.")

        # 1. Get the resolution from the selected video format for the final response
        video_format = next(
            (f for f in formats if f.get("format_id") == video_format_id), None
        )

        if not video_format:
            raise ValueError(f"Video format ID {video_format_id} not found.")

        # We get the height to honor the user's resolution choice.
        height = video_format.get("height")
        resolution = video_format.get("resolution")

        # 2. Build a robust format selector for yt-dlp.
        # Find the best MP4 video at this height and the best M4A audio.
        # If that fails, find the best of any format and let ffmpeg convert it to MP4.
        # More resilient than picking a specific format ID
        format_selector = (
            f"bestvideo[height={height}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        )

        # 3. Create a temporary file path for yt-dlp to write to
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            output_path = temp_file.name

        # 4. Configure yt-dlp with smart selector.
        ydl_opts = {
            "format": format_selector,
            "download_ranges": yt_dlp.utils.download_range_func(
                None, [(start_seconds, end_seconds)]
            ),
            "outtmpl": output_path,
            "merge_output_format": "mp4",  # Ensure the final output is always MP4
            "quiet": True,
            "no_warnings": True,
            "overwrites": True,
        }

        # 5. Execute the download with error handling
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Re-extract info with the new options to get the final format ID
                result_info = ydl.extract_info(url, download=True)
                # The format ID might be different from the one requested
                # As yt-dlp found the best working one.
                result_info.get("format_id")
        except yt_dlp.utils.DownloadError as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            # Check for the specific "not available" error
            if "requested format is not available" in str(e).lower():
                raise ValueError(
                    f"No working video format could be found for {resolution}."
                )
            raise ValueError(f"yt-dlp failed to download or process the sample: {e}")
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise e

        # --- Return the path and metadata ---
        return output_path, video_title, video_format_id, resolution
