from fastapi import FastAPI
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware
from yt_download_service.app.controllers import history_controller
from yt_download_service.env import SECRET_KEY
from yt_download_service.infrastructure.database.session import (
    AsyncSessionFactory,
)

from src.yt_download_service.app.controllers import auth_controller, video_controller

# OpenAPI Generation is handled automatically by FastAPI.
app = FastAPI(
    title="YT Download Service",
    description="Allows a google authenticated user to download videos from YouTube.",
    version="1.0.0",
    contact={"name": "Jean Motte", "email": "jijimotte@gmail.com"},
)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.include_router(auth_controller.router, prefix="/api/auth", tags=["Auth"])
app.include_router(video_controller.router, prefix="/api/video", tags=["Video"])
app.include_router(history_controller.router, prefix="/api/history", tags=["History"])


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.on_event("startup")
async def test_db_connection():
    """Test database connection on startup using an async session."""
    print("Testing database connection...")
    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        print("✅ Database connection successful.")
    except Exception as e:
        print(f"❌ Failed to connect to the database: {e}")
