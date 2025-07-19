from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UUIdentifiedObjectModel(BaseModel):
    """Base model for objects with a UUID identifier."""

    id: UUID


class TimedObjectModel(BaseModel):
    """Base model for objects with creation and update timestamps."""

    created_at: datetime | None
    updated_at: datetime | None
