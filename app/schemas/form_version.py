from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FormVersionCreate(BaseModel):
    form_id: UUID
    version_number: int
    is_active: bool = True


class FormVersionResponse(BaseModel):
    id: UUID
    form_id: UUID
    version_number: int
    is_active: bool
    published_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)