from urllib.parse import urljoin
from src.yt_download_service.infrastructure.database import env

SQLALCHEMY_DATABASE_URL = f"postgresql://{env.DB_USER}:{env.DB_PASS}@{env.DB_HOST}:{env.DB_PORT}/{env.DB_NAME}"
