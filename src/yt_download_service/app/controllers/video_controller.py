from fastapi import APIRouter

router = APIRouter()


@router.post("/download")
async def download_video(yt_video_id: str, start_time: int, end_time: int):
    """Endpoint to download a segment of a YouTube video."""
    # This will be implemented later
    return {"message": "Download endpoint"}
