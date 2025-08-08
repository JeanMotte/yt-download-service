from pydantic import BaseModel


class GoogleToken(BaseModel):
    """Model for Google OAuth token."""

    token: str
