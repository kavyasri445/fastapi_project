from uuid import UUID

from pydantic import BaseModel


class FieldOptionCreate(BaseModel):
    field_id: UUID
    option_label: str
    option_value: str
    display_order: int


class FieldOptionResponse(BaseModel):
    id: UUID
    field_id: UUID
    option_label: str
    option_value: str
    display_order: int

    class Config:
        from_attributes = True