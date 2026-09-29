import uuid
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.submission import Submission
from app.models.response_value import ResponseValue
from app.models.audit_log import AuditLog


router = APIRouter(
    prefix="/responses",
    tags=["Response Management"]
)


# =========================================================
# BULK DELETE REQUEST
# =========================================================

class BulkDeleteRequest(BaseModel):
    response_ids: list[uuid.UUID]


# =========================================================
# RETENTION REQUEST
# =========================================================

class RetentionRequest(BaseModel):
    days: int = Field(
        ...,
        gt=0,
        description="Archive responses older than this many days."
    )


# =========================================================
# BULK DELETE RESPONSES
# =========================================================

@router.delete("/bulk")
def bulk_delete_responses(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db)
):

    if not request.response_ids:
        raise HTTPException(
            status_code=400,
            detail="No response IDs were provided."
        )

    deleted_response_ids = []
    deleted_count = 0

    for response_id in request.response_ids:

        submission = (
            db.query(Submission)
            .filter(
                Submission.response_id == response_id
            )
            .first()
        )

        if submission is None:
            continue

        # -------------------------------------------------
        # Delete response values first
        # -------------------------------------------------

        db.query(ResponseValue).filter(
            ResponseValue.submission_id == submission.id
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # Create audit log
        # -------------------------------------------------

        audit_log = AuditLog(
            user_id=None,
            action="DELETE",
            entity_type="Submission",
            entity_id=str(submission.id),
            details=json.dumps({
                "response_id": str(response_id),
                "deleted_at": datetime.utcnow().isoformat()
            })
        )

        db.add(audit_log)

        # -------------------------------------------------
        # Delete submission
        # -------------------------------------------------

        db.delete(submission)

        deleted_response_ids.append(
            str(response_id)
        )

        deleted_count += 1

    db.commit()

    return {
        "message": "Responses deleted successfully.",
        "deleted_count": deleted_count,
        "deleted_response_ids": deleted_response_ids
    }


# =========================================================
# AUTO-ARCHIVE RESPONSES
# =========================================================

@router.post("/archive")
def archive_old_responses(
    request: RetentionRequest,
    db: Session = Depends(get_db)
):

    cutoff_date = (
        datetime.utcnow()
        - timedelta(days=request.days)
    )

    old_submissions = (
        db.query(Submission)
        .filter(
            Submission.submitted_at < cutoff_date,
            Submission.is_archived == False
        )
        .all()
    )

    archived_count = 0
    archived_response_ids = []

    for submission in old_submissions:

        submission.is_archived = True
        submission.archived_at = datetime.utcnow()

        if submission.response_id:
            archived_response_ids.append(
                str(submission.response_id)
            )

        archived_count += 1

    # -----------------------------------------------------
    # Audit log for retention action
    # -----------------------------------------------------

    if archived_count > 0:

        audit_log = AuditLog(
            user_id=None,
            action="ARCHIVE",
            entity_type="Submission",
            entity_id=None,
            details=json.dumps({
                "retention_days": request.days,
                "archived_count": archived_count,
                "archived_at": datetime.utcnow().isoformat(),
                "response_ids": archived_response_ids
            })
        )

        db.add(audit_log)

    db.commit()

    return {
        "message": "Old responses archived successfully.",
        "retention_days": request.days,
        "cutoff_date": cutoff_date,
        "archived_count": archived_count,
        "archived_response_ids": archived_response_ids
    }