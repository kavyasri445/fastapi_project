from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.submission import Submission
from app.models.form_version import FormVersion
from app.models.conditional_rule import ConditionalRule
from app.models.response_value import ResponseValue

from app.schemas.submission import (
    SubmissionCreate,
    SubmissionResponse
)


router = APIRouter(
    prefix="/submissions",
    tags=["Submissions"]
)


# =========================================================
# CREATE SUBMISSION
# =========================================================

@router.post("/", response_model=SubmissionResponse)
def create_submission(
    submission: SubmissionCreate,
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. CHECK FORM VERSION
    # =====================================================

    form_version = db.query(FormVersion).filter(
        FormVersion.id == submission.form_version_id
    ).first()

    if not form_version:
        raise HTTPException(
            status_code=404,
            detail="Form version not found"
        )

    # =====================================================
    # 2. GET CONDITIONAL RULES
    # =====================================================

    rules = db.query(ConditionalRule).filter(
        ConditionalRule.form_id == form_version.form_id
    ).all()

    print("Conditional rules found:", len(rules))

    # =====================================================
    # 3. CREATE SUBMITTED VALUE LOOKUP
    # =====================================================

    submitted_values = {
        str(item.field_id): item.value
        for item in submission.response_values
    }

    print("Submitted values:", submitted_values)

    # =====================================================
    # 4. EVALUATE CONDITIONAL RULES
    # =====================================================

    hidden_fields = set()
    required_fields = set()

    for rule in rules:

        trigger_field_id = str(
            rule.trigger_field_id
        )

        target_field_id = str(
            rule.target_field_id
        )

        trigger_value = submitted_values.get(
            trigger_field_id
        )

        comparison_value = rule.comparison_value

        operator = rule.operator

        print(
            "Evaluating rule:",
            trigger_value,
            operator,
            comparison_value
        )

        # -------------------------------------------------
        # EQUALS
        # -------------------------------------------------

        if operator == "equals":

            condition_true = (
                str(trigger_value)
                == str(comparison_value)
            )

        # -------------------------------------------------
        # NOT EQUALS
        # -------------------------------------------------

        elif operator == "not_equals":

            condition_true = (
                str(trigger_value)
                != str(comparison_value)
            )

        # -------------------------------------------------
        # CONTAINS
        # -------------------------------------------------

        elif operator == "contains":

            condition_true = (
                trigger_value is not None
                and str(comparison_value)
                in str(trigger_value)
            )

        # -------------------------------------------------
        # GREATER THAN
        # -------------------------------------------------

        elif operator == "greater_than":

            try:

                condition_true = (
                    float(trigger_value)
                    > float(comparison_value)
                )

            except (TypeError, ValueError):

                condition_true = False

        # -------------------------------------------------
        # IS EMPTY
        # -------------------------------------------------

        elif operator == "is_empty":

            condition_true = (
                trigger_value is None
                or str(trigger_value).strip() == ""
            )

        # -------------------------------------------------
        # INVALID OPERATOR
        # -------------------------------------------------

        else:

            raise HTTPException(
                status_code=400,
                detail=f"Invalid operator: {operator}"
            )

        print(
            "Condition result:",
            condition_true
        )

        # =================================================
        # 5. APPLY RULE ACTION
        # =================================================

        if condition_true:

            if rule.action == "show":

                hidden_fields.discard(
                    target_field_id
                )

            elif rule.action == "hide":

                hidden_fields.add(
                    target_field_id
                )

            elif rule.action == "require":

                required_fields.add(
                    target_field_id
                )

            else:

                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid action: {rule.action}"
                )

    # =====================================================
    # 6. VALIDATE HIDDEN FIELDS
    # =====================================================

    for field_id in hidden_fields:

        value = submitted_values.get(
            field_id
        )

        if (
            value is not None
            and str(value).strip() != ""
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Field {field_id} is hidden "
                    "and must not contain a value"
                )
            )

    # =====================================================
    # 7. VALIDATE CONDITIONALLY REQUIRED FIELDS
    # =====================================================

    for field_id in required_fields:

        value = submitted_values.get(
            field_id
        )

        if (
            value is None
            or str(value).strip() == ""
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Field {field_id} is required"
                )
            )

    # =====================================================
    # 8. CREATE SUBMISSION
    # =====================================================

    new_submission = Submission(
        form_version_id=submission.form_version_id,
        response_id=submission.response_id,
        completion_time_seconds=(
            submission.completion_time_seconds
        )
    )

    db.add(new_submission)

    # Get new_submission.id before commit
    db.flush()

    # =====================================================
    # 9. SAVE RESPONSE VALUES
    # =====================================================

    for item in submission.response_values:

        response_value = ResponseValue(
            submission_id=new_submission.id,
            field_id=item.field_id,
            value=item.value
        )

        db.add(response_value)

    # =====================================================
    # 10. COMMIT
    # =====================================================

    db.commit()

    db.refresh(new_submission)

    return new_submission


# =========================================================
# GET SUBMISSIONS
# =========================================================

@router.get(
    "/",
    response_model=list[SubmissionResponse]
)
def get_submissions(
    db: Session = Depends(get_db)
):

    return db.query(Submission).all()