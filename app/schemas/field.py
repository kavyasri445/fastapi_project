from uuid import UUID

from pydantic import BaseModel


class FieldCreate(BaseModel):
    form_version_id: UUID
    label: str
    field_type: str
    placeholder: str | None = None
    is_required: bool = False
    display_order: int
    validation_config: dict | None = None


class FieldResponse(BaseModel):
    id: UUID
    form_version_id: UUID
    label: str
    field_type: str
    placeholder: str | None = None
    is_required: bool
    display_order: int
    validation_config: dict | None = None

    class Config:
        from_attributes = True