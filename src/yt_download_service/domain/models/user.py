from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Base model for user data."""

    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None


class UserCreate(UserBase):
    """Model for creating a new user."""

    model_config = ConfigDict(from_attributes=True)


class UserRead(UserBase):
    """Model for reading user data from the database."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
