from src.yt_download_service.app.utils.env import get_or_raise_env

DB_NAME = get_or_raise_env("DB_NAME")
DB_HOST = get_or_raise_env("DB_HOST")
DB_PORT = get_or_raise_env("DB_PORT")
DB_USER = get_or_raise_env("DB_USER")
DB_PASS = get_or_raise_env("DB_PASS")
