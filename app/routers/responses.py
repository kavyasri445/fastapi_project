import csv
import io
import uuid
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import String, or_
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.form import Form
from app.models.form_version import FormVersion
from app.models.field import Field
from app.models.submission import Submission
from app.models.response_value import ResponseValue


router = APIRouter(
    prefix="/forms",
    tags=["Responses"]
)


# =========================================================
# GET FORM RESPONSES
#
# GET /forms/{form_id}/responses
#
# Supports:
# - Pagination
# - Date range filtering
# - Completion status filtering
# - Field value filtering
# - Search
# - Response ID fallback for older submissions
# =========================================================

@router.get("/{form_id}/responses")
def get_form_responses(
    form_id: uuid.UUID,

    # -----------------------------------------------------
    # Pagination
    # -----------------------------------------------------

    page: int = Query(
        default=1,
        ge=1,
        description="Page number"
    ),

    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of responses per page"
    ),

    # -----------------------------------------------------
    # Date filtering
    # -----------------------------------------------------

    start_date: date | None = Query(
        default=None,
        description="Return submissions from this date"
    ),

    end_date: date | None = Query(
        default=None,
        description="Return submissions up to this date"
    ),

    # -----------------------------------------------------
    # Completion status
    # -----------------------------------------------------

    status: str | None = Query(
        default=None,
        description="Filter by completed or incomplete"
    ),

    # -----------------------------------------------------
    # Field value filtering
    # -----------------------------------------------------

    field_id: uuid.UUID | None = Query(
        default=None,
        description="Field ID to filter by"
    ),

    field_value: str | None = Query(
        default=None,
        description="Field value to match"
    ),

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    search: str | None = Query(
        default=None,
        description="Search response values, response ID, or submission ID"
    ),

    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. CHECK FORM
    # =====================================================

    form = (
        db.query(Form)
        .filter(
            Form.id == form_id
        )
        .first()
    )

    if form is None:

        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    # =====================================================
    # 2. VALIDATE STATUS
    # =====================================================

    if status is not None:

        status = status.lower().strip()

        if status not in [
            "completed",
            "incomplete"
        ]:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid status. "
                    "Use 'completed' or 'incomplete'."
                )
            )

    # =====================================================
    # 3. VALIDATE DATE RANGE
    # =====================================================

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):

        raise HTTPException(
            status_code=400,
            detail="Start date cannot be after end date"
        )

    # =====================================================
    # 4. VALIDATE FIELD
    # =====================================================

    if field_id is not None:

        field_exists = (
            db.query(Field)
            .join(
                FormVersion,
                Field.form_version_id ==
                FormVersion.id
            )
            .filter(
                Field.id == field_id,
                FormVersion.form_id == form_id
            )
            .first()
        )

        if field_exists is None:

            raise HTTPException(
                status_code=404,
                detail="Field does not belong to this form"
            )

    # =====================================================
    # 5. GET FORM VERSION IDs
    # =====================================================

    form_version_ids = [
        version.id
        for version in (
            db.query(FormVersion)
            .filter(
                FormVersion.form_id == form_id
            )
            .all()
        )
    ]

    # =====================================================
    # 6. NO VERSIONS
    # =====================================================

    if not form_version_ids:

        return {
            "form_id": str(form_id),
            "form_title": form.title,
            "page": page,
            "page_size": page_size,
            "total": 0,
            "total_pages": 0,
            "has_next": False,
            "has_previous": False,
            "responses": []
        }

    # =====================================================
    # 7. BUILD BASE QUERY
    # =====================================================

    query = (
        db.query(Submission)
        .filter(
            Submission.form_version_id.in_(
                form_version_ids
            )
        )
    )

    # =====================================================
    # 8. DATE RANGE FILTER
    # =====================================================

    if start_date is not None:

        start_datetime = datetime.combine(
            start_date,
            datetime.min.time()
        )

        query = query.filter(
            Submission.submitted_at >= start_datetime
        )

    if end_date is not None:

        end_datetime = datetime.combine(
            end_date + timedelta(days=1),
            datetime.min.time()
        )

        query = query.filter(
            Submission.submitted_at < end_datetime
        )

    # =====================================================
    # 9. COMPLETION STATUS FILTER
    # =====================================================

    if status == "completed":

        query = query.filter(
            Submission.completion_time_seconds.isnot(None),
            Submission.completion_time_seconds > 0
        )

    elif status == "incomplete":

        query = query.filter(
            or_(
                Submission.completion_time_seconds.is_(None),
                Submission.completion_time_seconds <= 0
            )
        )

    # =====================================================
    # 10. FIELD VALUE FILTER
    # =====================================================

    if (
        field_id is not None
        and field_value is not None
    ):

        field_value_text = field_value.strip()

        if field_value_text:

            matching_submission_ids = (
                db.query(
                    ResponseValue.submission_id
                )
                .filter(
                    ResponseValue.field_id == field_id,
                    ResponseValue.value.ilike(
                        f"%{field_value_text}%"
                    )
                )
                .subquery()
            )

            query = query.filter(
                Submission.id.in_(
                    matching_submission_ids
                )
            )

    # =====================================================
    # 11. SEARCH RESPONSE DATA
    #
    # Search can match:
    # - Response values
    # - response_id
    # - submission_id
    #
    # submission_id is important for older records where
    # response_id is NULL.
    # =====================================================

    if search is not None:

        search_text = search.strip()

        if search_text:

            matching_submission_ids = (
                db.query(
                    ResponseValue.submission_id
                )
                .filter(
                    ResponseValue.value.ilike(
                        f"%{search_text}%"
                    )
                )
                .subquery()
            )

            response_id_condition = (
                Submission.response_id.cast(
                    String
                ).ilike(
                    f"%{search_text}%"
                )
            )

            submission_id_condition = (
                Submission.id.cast(
                    String
                ).ilike(
                    f"%{search_text}%"
                )
            )

            query = query.filter(
                or_(
                    Submission.id.in_(
                        matching_submission_ids
                    ),
                    response_id_condition,
                    submission_id_condition
                )
            )

    # =====================================================
    # 12. TOTAL COUNT
    # =====================================================

    total = query.count()

    # =====================================================
    # 13. CALCULATE TOTAL PAGES
    # =====================================================

    total_pages = (
        (total + page_size - 1)
        // page_size
    )

    # =====================================================
    # 14. PAGINATION
    # =====================================================

    offset = (
        (page - 1)
        * page_size
    )

    submissions = (
        query
        .order_by(
            Submission.submitted_at.desc()
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # =====================================================
    # 15. BUILD RESPONSE DATA
    # =====================================================

    response_list = []

    for submission in submissions:

        # -------------------------------------------------
        # Get form version
        # -------------------------------------------------

        version = (
            db.query(FormVersion)
            .filter(
                FormVersion.id ==
                submission.form_version_id
            )
            .first()
        )

        # -------------------------------------------------
        # Get response values
        # -------------------------------------------------

        values = (
            db.query(ResponseValue)
            .filter(
                ResponseValue.submission_id ==
                submission.id
            )
            .all()
        )

        # -------------------------------------------------
        # Build response data
        # -------------------------------------------------

        response_data = {}

        for response_value in values:

            field = (
                db.query(Field)
                .filter(
                    Field.id ==
                    response_value.field_id
                )
                .first()
            )

            if field is not None:

                response_data[
                    str(field.id)
                ] = {
                    "field_id":
                        str(field.id),

                    "field_label":
                        field.label,

                    "value":
                        response_value.value
                }

        # -------------------------------------------------
        # Determine submission status
        # -------------------------------------------------

        if (
            submission.completion_time_seconds
            is not None
            and
            submission.completion_time_seconds > 0
        ):

            submission_status = "Completed"

        else:

            submission_status = "Incomplete"

        # -------------------------------------------------
        # IMPORTANT:
        #
        # Use response_id when available.
        # Otherwise use submission.id.
        #
        # This removes "-" from older records.
        # -------------------------------------------------

        display_response_id = (
            str(submission.response_id)
            if submission.response_id
            else str(submission.id)
        )

        # -------------------------------------------------
        # Add response to list
        # -------------------------------------------------

        response_list.append({

            "submission_id":
                str(submission.id),

            "response_id":
                display_response_id,

            "submitted_at":
                submission.submitted_at,

            "status":
                submission_status,

            "completion_time_seconds":
                submission.completion_time_seconds,

            "form_version_id":
                (
                    str(submission.form_version_id)
                    if submission.form_version_id
                    else None
                ),

            "version_number":
                (
                    version.version_number
                    if version
                    else None
                ),

            "response_data":
                response_data
        })

    # =====================================================
    # 16. RETURN PAGINATED RESPONSE
    # =====================================================

    return {

        "form_id":
            str(form_id),

        "form_title":
            form.title,

        "page":
            page,

        "page_size":
            page_size,

        "total":
            total,

        "total_pages":
            total_pages,

        "has_next":
            page < total_pages,

        "has_previous":
            page > 1,

        "responses":
            response_list
    }


# =========================================================
# EXPORT RESPONSES - HELPER FUNCTION
# =========================================================

def build_export_data(
    form_id: uuid.UUID,
    db: Session
):

    # =====================================================
    # 1. CHECK FORM
    # =====================================================

    form = (
        db.query(Form)
        .filter(
            Form.id == form_id
        )
        .first()
    )

    if form is None:

        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    # =====================================================
    # 2. GET ALL FORM VERSIONS
    # =====================================================

    versions = (
        db.query(FormVersion)
        .filter(
            FormVersion.form_id == form_id
        )
        .order_by(
            FormVersion.version_number.asc()
        )
        .all()
    )

    if not versions:

        return form, [], []

    # =====================================================
    # 3. GET ALL SUBMISSIONS
    # =====================================================

    version_ids = [
        version.id
        for version in versions
    ]

    submissions = (
        db.query(Submission)
        .filter(
            Submission.form_version_id.in_(
                version_ids
            )
        )
        .order_by(
            Submission.submitted_at.asc()
        )
        .all()
    )

    # =====================================================
    # 4. GET ALL FIELDS
    # =====================================================

    fields = (
        db.query(Field)
        .filter(
            Field.form_version_id.in_(
                version_ids
            )
        )
        .order_by(
            Field.form_version_id.asc(),
            Field.display_order.asc()
        )
        .all()
    )

    # =====================================================
    # 5. BUILD FIELD MAP
    # =====================================================

    field_map = {}

    for field in fields:

        field_map[
            field.id
        ] = field

    # =====================================================
    # 6. BUILD EXPORT ROWS
    # =====================================================

    export_rows = []

    for submission in submissions:

        values = (
            db.query(ResponseValue)
            .filter(
                ResponseValue.submission_id ==
                submission.id
            )
            .all()
        )

        # ---------------------------------------------
        # Response metadata
        # ---------------------------------------------

        row = {

            "response_id":
                (
                    str(submission.response_id)
                    if submission.response_id
                    else str(submission.id)
                ),

            "submitted_at":
                (
                    submission.submitted_at.isoformat()
                    if submission.submitted_at
                    else None
                ),

            "status":
                (
                    "Completed"
                    if (
                        submission.completion_time_seconds
                        is not None
                        and
                        submission.completion_time_seconds > 0
                    )
                    else "Incomplete"
                )
        }

        # ---------------------------------------------
        # Add submitted field values
        # ---------------------------------------------

        for response_value in values:

            field = field_map.get(
                response_value.field_id
            )

            if field is None:
                continue

            field_label = field.label

            # -----------------------------------------
            # Keep unique field labels
            # -----------------------------------------

            if field_label not in row:

                row[field_label] = (
                    response_value.value
                )

            else:

                version = (
                    db.query(FormVersion)
                    .filter(
                        FormVersion.id ==
                        field.form_version_id
                    )
                    .first()
                )

                if version:

                    versioned_label = (
                        f"{field_label} "
                        f"(Version {version.version_number})"
                    )

                    row[versioned_label] = (
                        response_value.value
                    )

                else:

                    row[
                        f"{field_label} "
                        f"({field.id})"
                    ] = response_value.value

        export_rows.append(row)

    return form, fields, export_rows


# =========================================================
# EXPORT RESPONSES AS CSV
#
# GET /forms/{form_id}/export/csv
# =========================================================

@router.get("/{form_id}/export/csv")
def export_responses_csv(
    form_id: uuid.UUID,
    db: Session = Depends(get_db)
):

    # =====================================================
    # BUILD EXPORT DATA
    # =====================================================

    form, fields, export_rows = (
        build_export_data(
            form_id,
            db
        )
    )

    # =====================================================
    # NO RESPONSES
    # =====================================================

    if not export_rows:

        csv_buffer = io.StringIO()

        writer = csv.writer(
            csv_buffer
        )

        writer.writerow([
            "Response ID",
            "Submitted Date",
            "Status"
        ])

        csv_content = (
            csv_buffer.getvalue()
        )

        csv_buffer.close()

        return StreamingResponse(

            iter([
                csv_content
            ]),

            media_type="text/csv",

            headers={
                "Content-Disposition":
                    (
                        'attachment; '
                        f'filename="{form.title}_responses.csv"'
                    )
            }
        )

    # =====================================================
    # CREATE CSV
    # =====================================================

    csv_buffer = io.StringIO()

    writer = csv.writer(
        csv_buffer
    )

    # =====================================================
    # BUILD COLUMN HEADERS
    # =====================================================

    headers = [
        "Response ID",
        "Submitted Date",
        "Status"
    ]

    for row in export_rows:

        for key in row.keys():

            if key not in headers:

                headers.append(key)

    # =====================================================
    # WRITE HEADER
    # =====================================================

    writer.writerow(
        headers
    )

    # =====================================================
    # WRITE DATA
    # =====================================================

    for row in export_rows:

        writer.writerow([
            row.get(
                header,
                ""
            )
            for header in headers
        ])

    csv_content = (
        csv_buffer.getvalue()
    )

    csv_buffer.close()

    # =====================================================
    # RETURN DOWNLOADABLE CSV
    # =====================================================

    filename = (
        f"{form.title}_responses.csv"
        .replace(" ", "_")
    )

    return StreamingResponse(

        iter([
            csv_content
        ]),

        media_type="text/csv",

        headers={
            "Content-Disposition":
                (
                    "attachment; "
                    f'filename="{filename}"'
                )
        }
    )


# =========================================================
# EXPORT RESPONSES AS JSON
#
# GET /forms/{form_id}/export/json
# =========================================================

@router.get("/{form_id}/export/json")
def export_responses_json(
    form_id: uuid.UUID,
    db: Session = Depends(get_db)
):

    # =====================================================
    # BUILD EXPORT DATA
    # =====================================================

    form, fields, export_rows = (
        build_export_data(
            form_id,
            db
        )
    )

    # =====================================================
    # RETURN DOWNLOADABLE JSON
    # =====================================================

    filename = (
        f"{form.title}_responses.json"
        .replace(" ", "_")
    )

    return JSONResponse(

        content=export_rows,

        headers={
            "Content-Disposition":
                (
                    "attachment; "
                    f'filename="{filename}"'
                )
        }
    )