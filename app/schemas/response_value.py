from uuid import UUID
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ResponseValueCreate(BaseModel):
    submission_id: UUID
    field_id: UUID
    value: Any


class ResponseValueResponse(BaseModel):
    id: UUID
    submission_id: UUID
    field_id: UUID
    value: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )