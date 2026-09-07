from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FormCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "draft"
    created_by: UUID


class FormUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class FormResponse(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)