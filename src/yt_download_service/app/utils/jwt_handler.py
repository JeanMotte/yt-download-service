import os
from datetime import datetime, timedelta, timezone
from typing import Any, cast

from jose import JWTError, jwt
from pydantic import BaseModel

# --- Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class TokenResponse(BaseModel):
    """Pydantic model for the token response."""

    access_token: str
    token_type: str = "bearer"


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    return cast(str, jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode a JWT access token.

    Raises JWTError if the token is invalid or expired.
    """
    try:
        return cast(
            dict[str, Any], jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        )
    except JWTError as e:
        raise e
