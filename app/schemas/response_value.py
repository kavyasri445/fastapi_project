from uuid import UUID

from pydantic import BaseModel


class ResponseValueCreate(BaseModel):
    submission_id: UUID
    field_id: UUID
    value: str | None = None


class ResponseValueResponse(BaseModel):
    id: UUID
    submission_id: UUID
    field_id: UUID
    value: str | None
    created_at: object

    class Config:
        from_attributes = True