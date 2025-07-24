from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from yt_download_service.app.domain.schemas import (
    DownloadRequest,
    DownloadSampleRequest,
    Stream,
    VideoURL,
)
from yt_download_service.app.use_cases.video_service import VideoService
from yt_download_service.app.utils.dependencies import get_current_user_from_token
from yt_download_service.domain.models.user import UserRead

router = APIRouter()
video_service = VideoService()


@router.post("/formats", response_model=List[Stream])
async def get_formats(
    video_url: VideoURL, current_user: UserRead = Depends(get_current_user_from_token)
):
    """Endpoint to get all available video formats for a given YouTube video URL."""
    try:
        formats = await video_service.get_video_formats(video_url.url)
        return formats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download")
async def download_full_video(
    request: DownloadRequest,
    current_user: UserRead = Depends(get_current_user_from_token),
):
    """Endpoint to download a YouTube video, optionally with a specific format."""
    try:
        video_file = await video_service.download_full_video(
            request.url, request.format_id
        )  # noqa: E501

        headers = {"Content-Disposition": 'attachment; filename="video.mp4"'}
        return StreamingResponse(video_file, media_type="video/mp4", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download/sample")
async def download_video_sample(
    request: DownloadSampleRequest,
    current_user: UserRead = Depends(get_current_user_from_token),
):
    """Endpoint to download a sample of a YouTube video."""
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
        video_file = await video_service.download_video_sample(
            url=request.url,
            format_id=request.format_id,
            start_time=request.start_time,
            end_time=request.end_time,
        )

        headers = {"Content-Disposition": 'attachment; filename="video_sample.mp4"'}
        return StreamingResponse(video_file, media_type="video/mp4", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
