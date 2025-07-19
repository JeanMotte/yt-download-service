from fastapi import FastAPI
from psycopg2 import OperationalError
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware
from yt_download_service.env import SECRET_KEY
from yt_download_service.infrastructure.database.session import SessionFactory

from src.yt_download_service.app.controllers import auth_controller, video_controller

# OpenAPI Generation is handled automatically by FastAPI.
# You can customize it here.
app = FastAPI(
    title="YT Download Service",
    description="A demonstration of FastAPI with Clean Architecture.",
    version="1.0.0",
)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.include_router(auth_controller.router, prefix="/api/auth", tags=["Auth"])
app.include_router(video_controller.router, prefix="/api/video", tags=["Video"])


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.on_event("startup")
def test_db_connection():
    """Test database connection on startup."""
    try:
        db = SessionFactory()
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database connection successful.")
    except OperationalError as e:
        print("❌ Failed to connect to the database:", str(e))
