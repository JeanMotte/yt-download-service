import yt_dlp
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
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
    """Download a video and logs the action in the background."""
    try:
        # 1. Download the video and get metadata
        result = await video_service.download_full_video(request.url, request.format_id)

        # 2. Add the history-saving task to the background
        background_tasks.add_task(
            history_service_instance.create_history_entry,
            db,
            user_id=current_user.id,
            video_url=request.url,
            video_title=result.video_title,
            format_id=result.final_format_id,
            resolution=result.resolution,
        )

        # 3. Return the file stream to the user immediately
        headers = {
            "Content-Disposition": f'attachment; filename="{result.video_title}.mp4"'
        }
        return StreamingResponse(
            result.file_buffer, media_type="video/mp4", headers=headers
        )
    except (ValueError, yt_dlp.utils.DownloadError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download/sample")
async def download_video_sample(
    request: DownloadSampleRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user_from_token),
):
    """Download a video sample and logs the action in the background."""
    start_seconds = video_service._time_str_to_seconds(request.start_time)
    end_seconds = video_service._time_str_to_seconds(request.end_time)

    # Max 30 seconds allowed
    if end_seconds - start_seconds > 30:
        raise HTTPException(
            status_code=400,
            detail="The sample duration cannot exceed 30 seconds.",
        )

    if start_seconds >= end_seconds:
        raise HTTPException(
            status_code=400,
            detail="Start time must be less than end time.",
        )
    try:
        # 1. Download the sample and get metadata
        result = await video_service.download_video_sample(
            url=request.url,
            format_id=request.format_id,
            start_time=request.start_time,
            end_time=request.end_time,
        )

        # 2. Add the history-saving task to the background
        background_tasks.add_task(
            history_service_instance.create_history_entry,
            db,
            user_id=current_user.id,
            video_url=request.url,
            video_title=result.video_title,
            format_id=result.final_format_id,
            resolution=result.resolution,
            start_time_str=request.start_time,
            end_time_str=request.end_time,
        )

        # 3. Return the file stream
        filename = f"{result.video_title}_sample.mp4"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(
            result.file_buffer, media_type="video/mp4", headers=headers
        )
    except (ValueError, yt_dlp.utils.DownloadError) as e:
        raise HTTPException(status_code=400, detail=str(e))
