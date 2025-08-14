import os

import yt_dlp
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from yt_download_service.app.domain.schemas import (
    DownloadRequest,
    DownloadSampleRequest,
    FormatsResponse,
    VideoURL,
)
from yt_download_service.app.use_cases.history_service import HistoryService
from yt_download_service.app.use_cases.video_service import VideoService
from yt_download_service.app.utils.dependencies import get_current_user_from_token
from yt_download_service.app.utils.file_utils import sanitize_filename
from yt_download_service.domain.models.user import UserRead
from yt_download_service.infrastructure.database.session import get_db_session

router = APIRouter()
video_service = VideoService()
history_service_instance = HistoryService()


@router.post("/formats", response_model=FormatsResponse)
async def get_formats(
    video_url: VideoURL, current_user: UserRead = Depends(get_current_user_from_token)
):
    """Endpoint to get processed and user-friendly video formats."""
    try:
        formats = await video_service.get_video_formats(video_url.url)
        return formats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download")
async def download_full_video(
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user_from_token),
):
    """Download a short video and returns it as a file attachment."""
    try:
        # 1. Download the video. The service now returns the path and metadata.
        (
            file_path,
            video_title,
            final_format_id,
            resolution,
        ) = await video_service.download_full_video(request.url, request.format_id)

        # 2. Add the history-saving task to the background
        background_tasks.add_task(
            history_service_instance.create_history_entry,
            db,
            user_id=current_user.id,
            video_url=request.url,
            video_title=video_title,
            format_id=final_format_id,
            resolution=resolution,
        )

        # 3. Background task to delete the temporary file after sending.
        background_tasks.add_task(os.remove, file_path)

        # 4. Return the file using FileResponse for efficient streaming.
        safe_filename = sanitize_filename(video_title)
        # The filename in the Content-Disposition header is a suggestion to the browser.
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",  # A generic binary type is safest
            filename=f"{safe_filename}.mp4",
        )
    except (ValueError, yt_dlp.utils.DownloadError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")


@router.post("/download/sample")
async def download_optimal_video_sample(
    request: DownloadSampleRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user_from_token),
):
    """Download a specific time-range."""
    start_seconds = video_service._time_str_to_seconds(request.start_time)
    end_seconds = video_service._time_str_to_seconds(request.end_time)

    if end_seconds - start_seconds > 180:  # Limit to 3 minutes
        raise HTTPException(
            status_code=400,
            detail="The sample duration cannot exceed 3 minutes.",
        )

    if start_seconds >= end_seconds:
        raise HTTPException(
            status_code=400,
            detail="Start time must be less than end time.",
        )
    try:
        # 1. Call the updated optimal download service method
        (
            file_path,
            video_title,
            final_format_id,
            resolution,
        ) = await video_service.download_optimal_sample(
            url=request.url,
            format_id=request.format_id,
            start_time=request.start_time,
            end_time=request.end_time,
        )

        # 2. Background task for history logging
        background_tasks.add_task(
            history_service_instance.create_history_entry,
            db,
            user_id=current_user.id,
            video_url=request.url,
            video_title=video_title,
            format_id=final_format_id,
            resolution=resolution,
            start_time_str=request.start_time,
            end_time_str=request.end_time,
        )

        # 3. Add background task to delete the temporary file
        background_tasks.add_task(os.remove, file_path)

        # 4. Return the file using FileResponse
        safe_filename = f"{sanitize_filename(video_title)}_sample.mp4"
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            filename=safe_filename,
        )
    except (ValueError, yt_dlp.utils.DownloadError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
