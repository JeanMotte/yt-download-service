from yt_download_service.app.utils.env import get_or_raise_env

SECRET_KEY = get_or_raise_env("SECRET_KEY")
