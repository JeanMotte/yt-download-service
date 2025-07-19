from fastapi import FastAPI

from src.yt_download_service.app.controllers import auth_controller, video_controller

# OpenAPI Generation is handled automatically by FastAPI.
# You can customize it here.
app = FastAPI(
    title="YT Download Service",
    description="A demonstration of FastAPI with Clean Architecture.",
    version="1.0.0",
)

app.include_router(auth_controller.router, prefix="/auth", tags=["Auth"])
app.include_router(video_controller.router, prefix="/video", tags=["Video"])


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
