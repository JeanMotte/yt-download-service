from yt_download_service.app.utils.env import get_or_raise_env

SQLALCHEMY_DATABASE_URL = get_or_raise_env("DB_URL")
