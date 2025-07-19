from uuid import UUID
from pydantic import BaseModel, ConfigDict
from polynom_api_template.commons.base_models import (
    UUIdentifiedObjectModel,
    TimedObjectModel,
)
from polynom_api_template.config import enums


class UserBaseModel(BaseModel):
    email: str
    last_name: str
    first_name: str
    role: enums.ROLE
    oidc_id: UUID | None = None


class UserCreateModel(UserBaseModel):
    pass


class UserModel(UserBaseModel, UUIdentifiedObjectModel, TimedObjectModel):
    model_config = ConfigDict(from_attributes=True)


class UserUpdateModel(BaseModel):
    email: str | None = None
    last_name: str | None = None
    first_name: str | None = None
    role: enums.ROLE | None = None
    oidc_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)
