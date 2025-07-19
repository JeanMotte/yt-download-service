from authlib.integrations.starlette_client import OAuth

from .env import get_or_raise_env

GOOGLE_CLIENT_ID = get_or_raise_env("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = get_or_raise_env("GOOGLE_CLIENT_SECRET")

oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
