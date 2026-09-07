import uuid

from pydantic import BaseModel, ConfigDict


class ConditionalRuleCreate(BaseModel):
    trigger_field_id: uuid.UUID
    operator: str
    comparison_value: str | None = None
    target_field_id: uuid.UUID
    action: str


class ConditionalRuleUpdate(BaseModel):
    trigger_field_id: uuid.UUID | None = None
    operator: str | None = None
    comparison_value: str | None = None
    target_field_id: uuid.UUID | None = None
    action: str | None = None


class ConditionalRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    form_id: uuid.UUID
    trigger_field_id: uuid.UUID
    operator: str
    comparison_value: str | None
    target_field_id: uuid.UUID
    action: str