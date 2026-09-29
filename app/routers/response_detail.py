import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.submission import Submission
from app.models.response_value import ResponseValue
from app.models.field import Field
from app.models.form_version import FormVersion
from app.models.form import Form


router = APIRouter(
    prefix="/responses",
    tags=["Response Details"]
)


# =========================================================
# GET INDIVIDUAL RESPONSE
#
# GET /responses/{response_id}
#
# The value can be:
# - submission.response_id
# - submission.id
#
# This allows older submissions that do not have a
# response_id to still be opened from the dashboard.
# =========================================================

@router.get("/{response_id}")
def get_response_detail(
    response_id: uuid.UUID,
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. FIND SUBMISSION
    #
    # First try the normal response_id.
    # If that does not exist, try submission.id.
    # =====================================================

    submission = (
        db.query(Submission)
        .filter(
            Submission.response_id == response_id
        )
        .first()
    )

    if submission is None:

        submission = (
            db.query(Submission)
            .filter(
                Submission.id == response_id
            )
            .first()
        )

    # =====================================================
    # 2. IF RESPONSE NOT FOUND
    # =====================================================

    if submission is None:

        raise HTTPException(
            status_code=404,
            detail="Response not found"
        )

    # =====================================================
    # 3. GET FORM VERSION
    # =====================================================

    version = (
        db.query(FormVersion)
        .filter(
            FormVersion.id ==
            submission.form_version_id
        )
        .first()
    )

    if version is None:

        raise HTTPException(
            status_code=404,
            detail="Form version not found"
        )

    # =====================================================
    # 4. GET FORM
    # =====================================================

    form = (
        db.query(Form)
        .filter(
            Form.id == version.form_id
        )
        .first()
    )

    # =====================================================
    # 5. GET ALL RESPONSE VALUES
    # =====================================================

    response_values = (
        db.query(ResponseValue)
        .filter(
            ResponseValue.submission_id ==
            submission.id
        )
        .all()
    )

    # =====================================================
    # 6. BUILD ANSWERS
    # =====================================================

    answers = []

    for response_value in response_values:

        field = (
            db.query(Field)
            .filter(
                Field.id ==
                response_value.field_id
            )
            .first()
        )

        if field is None:
            continue

        answers.append({

            "field_id":
                str(field.id),

            "field_label":
                field.label,

            "field_type":
                field.field_type,

            "value":
                response_value.value
        })

    # =====================================================
    # 7. DETERMINE STATUS
    # =====================================================

    if (
        submission.completion_time_seconds
        is not None
        and
        submission.completion_time_seconds > 0
    ):

        status = "Completed"

    else:

        status = "Incomplete"

    # =====================================================
    # 8. CREATE DISPLAY RESPONSE ID
    #
    # If response_id exists, use it.
    # Otherwise use submission.id.
    # =====================================================

    display_response_id = (
        str(submission.response_id)
        if submission.response_id
        else str(submission.id)
    )

    # =====================================================
    # 9. RETURN COMPLETE RESPONSE
    # =====================================================

    return {

        "response_id":
            display_response_id,

        "submission_id":
            str(submission.id),

        "form_id":
            (
                str(form.id)
                if form
                else None
            ),

        "form_title":
            (
                form.title
                if form
                else None
            ),

        "form_version_id":
            str(submission.form_version_id),

        "version_number":
            (
                version.version_number
                if version
                else None
            ),

        "submitted_at":
            submission.submitted_at,

        "status":
            status,

        "completion_time_seconds":
            submission.completion_time_seconds,

        "answers":
            answers
    }