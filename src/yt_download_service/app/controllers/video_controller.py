from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from yt_download_service.app.domain.schemas import Stream, VideoURL
from yt_download_service.app.use_cases.video_service import VideoService

router = APIRouter()
video_service = VideoService()


@router.post("/formats", response_model=List[Stream])
async def get_formats(video_url: VideoURL):
    """Endpoint to get all available video formats for a given YouTube video URL."""
    try:
        formats = video_service.get_video_formats(video_url.url)
        return formats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download")
async def download_video(video_url: VideoURL):
    """Endpoint to download a YouTube video in MP4 format."""
    try:
        video_file = video_service.download_video(video_url.url)
        return StreamingResponse(video_file, media_type="video/mp4")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
