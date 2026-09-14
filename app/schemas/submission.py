import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


# =========================================================
# PUBLIC RESPONSE VALUE
# =========================================================

class PublicResponseValueCreate(BaseModel):
    field_id: uuid.UUID
    value: Any


# =========================================================
# PUBLIC SUBMISSION
# =========================================================

class PublicSubmissionCreate(BaseModel):
    completion_time_seconds: int = 0
    response_values: list[PublicResponseValueCreate]


# =========================================================
# NORMAL RESPONSE VALUE
# =========================================================

class ResponseValueCreate(BaseModel):
    field_id: uuid.UUID
    value: Any


# =========================================================
# RESPONSE VALUE RESPONSE
# =========================================================

class ResponseValueResponse(BaseModel):
    id: uuid.UUID
    submission_id: uuid.UUID
    field_id: uuid.UUID
    value: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# NORMAL SUBMISSION
# =========================================================

class SubmissionCreate(BaseModel):
    form_version_id: uuid.UUID
    response_id: uuid.UUID | None = None
    completion_time_seconds: int = 0
    response_values: list[ResponseValueCreate]


# =========================================================
# SUBMISSION RESPONSE
# =========================================================

class SubmissionResponse(BaseModel):
    id: uuid.UUID
    form_version_id: uuid.UUID
    response_id: uuid.UUID | None
    submitted_at: datetime
    completion_time_seconds: int

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# SUBMISSION DETAIL
# =========================================================

class SubmissionDetailResponse(BaseModel):
    id: uuid.UUID
    form_version_id: uuid.UUID
    response_id: uuid.UUID | None
    submitted_at: datetime
    completion_time_seconds: int
    response_values: list[ResponseValueResponse]

    model_config = ConfigDict(
        from_attributes=True
    )