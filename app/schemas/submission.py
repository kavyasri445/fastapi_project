from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# SUBMITTED FIELD VALUE
# =========================================================

class ResponseValueCreate(BaseModel):
    field_id: UUID
    value: str | None = None


# =========================================================
# CREATE SUBMISSION
# =========================================================

class SubmissionCreate(BaseModel):
    form_version_id: UUID
    response_id: UUID | None = None
    completion_time_seconds: int | None = None

    # Answers submitted by the user
    response_values: list[ResponseValueCreate] = Field(
        default_factory=list
    )


# =========================================================
# SUBMISSION RESPONSE
# =========================================================

class SubmissionResponse(BaseModel):
    id: UUID
    form_version_id: UUID
    response_id: UUID | None = None
    submitted_at: datetime
    completion_time_seconds: int | None = None

    model_config = ConfigDict(from_attributes=True)