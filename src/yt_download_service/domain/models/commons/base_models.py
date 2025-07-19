from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class UUIdentifiedObjectModel(BaseModel):
    id: UUID


class TimedObjectModel(BaseModel):
    created_at: datetime | None
    updated_at: datetime | None
