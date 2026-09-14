import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.public_link import PublicLink
from app.models.form_version import FormVersion
from app.models.field import Field
from app.models.field_option import FieldOption
from app.models.submission import Submission
from app.models.response_value import ResponseValue

from app.schemas.submission import PublicSubmissionCreate


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/public/forms",
    tags=["Public Forms"]
)


# =========================================================
# SUBMIT PUBLIC FORM
# POST /public/forms/{slug}/submit
# =========================================================

@router.post("/{slug}/submit")
def submit_public_form(
    slug: str,
    submission_data: PublicSubmissionCreate,
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # 1. FIND PUBLIC LINK
    # -----------------------------------------------------

    public_link = (
        db.query(PublicLink)
        .filter(
            PublicLink.slug == slug,
            PublicLink.is_active.is_(True)
        )
        .first()
    )

    if public_link is None:
        raise HTTPException(
            status_code=404,
            detail="Public form not found or inactive"
        )

    # -----------------------------------------------------
    # 2. FIND FORM VERSION
    # -----------------------------------------------------

    form_version = (
        db.query(FormVersion)
        .filter(
            FormVersion.id == public_link.form_version_id,
            FormVersion.is_active.is_(True)
        )
        .first()
    )

    if form_version is None:
        raise HTTPException(
            status_code=404,
            detail="Published form version not found"
        )

    # -----------------------------------------------------
    # 3. GET FIELDS
    # -----------------------------------------------------

    fields = (
        db.query(Field)
        .filter(
            Field.form_version_id == form_version.id
        )
        .order_by(Field.display_order)
        .all()
    )

    if not fields:
        raise HTTPException(
            status_code=400,
            detail="No fields found for this form version"
        )

    # -----------------------------------------------------
    # 4. CHECK RESPONSE VALUES
    # -----------------------------------------------------

    if not submission_data.response_values:
        raise HTTPException(
            status_code=400,
            detail="No response values submitted"
        )

    # -----------------------------------------------------
    # 5. CHECK FIELD IDS
    # -----------------------------------------------------

    valid_field_ids = {
        field.id
        for field in fields
    }

    for item in submission_data.response_values:

        if item.field_id not in valid_field_ids:

            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid field",
                    "field_id": str(item.field_id)
                }
            )

    # -----------------------------------------------------
    # 6. CONVERT SUBMITTED VALUES TO DICTIONARY
    # -----------------------------------------------------

    submitted_values = {
        str(item.field_id): item.value
        for item in submission_data.response_values
    }

    validation_errors = {}

    # -----------------------------------------------------
    # 7. VALIDATE FIELDS
    # -----------------------------------------------------

    for field in fields:

        field_id = str(field.id)

        value = submitted_values.get(field_id)

        # -------------------------------------------------
        # REQUIRED
        # -------------------------------------------------

        if field.is_required:

            if value is None or value == "":

                validation_errors[field_id] = [
                    "This field is required"
                ]

                continue

        # -------------------------------------------------
        # OPTIONAL EMPTY
        # -------------------------------------------------

        if value is None or value == "":
            continue

        # -------------------------------------------------
        # DROPDOWN
        # -------------------------------------------------

        if field.field_type == "dropdown":

            options = (
                db.query(FieldOption)
                .filter(
                    FieldOption.field_id == field.id
                )
                .order_by(FieldOption.display_order)
                .all()
            )

            allowed_values = [
                str(option.option_value)
                for option in options
            ]

            if allowed_values:

                if str(value) not in allowed_values:

                    validation_errors[field_id] = [
                        "Invalid option. Allowed values: "
                        + ", ".join(allowed_values)
                    ]

        # -------------------------------------------------
        # CHECKBOX
        # -------------------------------------------------

        elif field.field_type == "checkbox":

            config = field.validation_config or {}

            if config.get("must_be_checked") is True:

                checked = (
                    value is True
                    or str(value).lower() == "true"
                )

                if not checked:

                    validation_errors[field_id] = [
                        "This field must be checked"
                    ]

        # -------------------------------------------------
        # RATING
        # -------------------------------------------------

        elif field.field_type == "rating":

            config = field.validation_config or {}

            minimum = config.get("min", 1)
            maximum = config.get("max", 5)

            try:

                rating = int(value)

                if rating < minimum or rating > maximum:

                    validation_errors[field_id] = [
                        f"Rating must be between "
                        f"{minimum} and {maximum}"
                    ]

            except (ValueError, TypeError):

                validation_errors[field_id] = [
                    "Rating must be a number"
                ]

    # -----------------------------------------------------
    # 8. VALIDATION ERROR
    # -----------------------------------------------------

    if validation_errors:

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Validation failed",
                "errors": validation_errors
            }
        )

    # -----------------------------------------------------
    # 9. CREATE RESPONSE ID
    # -----------------------------------------------------

    response_id = uuid.uuid4()

    # -----------------------------------------------------
    # 10. CREATE SUBMISSION
    # -----------------------------------------------------

    submission = Submission(
        form_version_id=form_version.id,
        response_id=response_id,
        completion_time_seconds=(
            submission_data.completion_time_seconds
        )
    )

    db.add(submission)

    # Generate submission.id
    db.flush()

    # -----------------------------------------------------
    # 11. SAVE RESPONSE VALUES
    # -----------------------------------------------------

    for item in submission_data.response_values:

        response_value = ResponseValue(
            submission_id=submission.id,
            field_id=item.field_id,
            value=str(item.value)
        )

        db.add(response_value)

    # -----------------------------------------------------
    # 12. COMMIT
    # -----------------------------------------------------

    try:

        db.commit()

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save submission: {str(e)}"
        )

    # -----------------------------------------------------
    # 13. REFRESH
    # -----------------------------------------------------

    db.refresh(submission)

    # -----------------------------------------------------
    # 14. SUCCESS
    # -----------------------------------------------------

    return {
        "message": "Form submitted successfully",
        "response_id": str(response_id),
        "submission_id": str(submission.id)
    }