import uuid
from collections import Counter, OrderedDict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.form import Form
from app.models.form_version import FormVersion
from app.models.field import Field
from app.models.field_option import FieldOption
from app.models.submission import Submission
from app.models.response_value import ResponseValue
from app.models.public_link import PublicLink
from app.models.form_start import FormStart


router = APIRouter(
    prefix="/forms",
    tags=["Analytics"]
)


# =========================================================
# START PUBLIC FORM
# POST /forms/public-start/{slug}
# =========================================================

@router.post("/public-start/{slug}")
def start_public_form(
    slug: str,
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. FIND ACTIVE PUBLIC LINK
    # =====================================================

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

    # =====================================================
    # 2. FIND ACTIVE FORM VERSION
    # =====================================================

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

    # =====================================================
    # 3. CREATE FORM START RECORD
    # =====================================================

    form_start = FormStart(
        form_version_id=form_version.id
    )

    db.add(form_start)

    # =====================================================
    # 4. SAVE FORM START
    # =====================================================

    try:

        db.commit()

    except Exception as e:

        db.rollback()

        print("FORM START DATABASE ERROR:")
        print(e)

        raise HTTPException(
            status_code=500,
            detail="Failed to record form start"
        )

    # =====================================================
    # 5. REFRESH RECORD
    # =====================================================

    db.refresh(form_start)

    # =====================================================
    # 6. RETURN START INFORMATION
    # =====================================================

    return {
        "message": "Form start recorded",
        "start_id": str(form_start.id),
        "form_version_id": str(form_version.id)
    }


# =========================================================
# GET FORM ANALYTICS
# GET /forms/{form_id}/analytics
# =========================================================

@router.get("/{form_id}/analytics")
def get_form_analytics(
    form_id: uuid.UUID,

    start_date: date | None = Query(
        default=None,
        description="Filter submissions from this date"
    ),

    end_date: date | None = Query(
        default=None,
        description="Filter submissions up to this date"
    ),

    form_version_id: uuid.UUID | None = Query(
        default=None,
        description="Filter analytics by form version"
    ),

    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. CHECK WHETHER FORM EXISTS
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
    # 2. VALIDATE DATE RANGE
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
    # 3. VALIDATE FORM VERSION
    # =====================================================

    if form_version_id is not None:

        selected_version = (
            db.query(FormVersion)
            .filter(
                FormVersion.id == form_version_id,
                FormVersion.form_id == form_id
            )
            .first()
        )

        if selected_version is None:

            raise HTTPException(
                status_code=404,
                detail="Form version not found for this form"
            )

    # =====================================================
    # 4. GET SUBMISSIONS
    # =====================================================

    submission_query = (
        db.query(Submission)
        .join(
            FormVersion,
            Submission.form_version_id == FormVersion.id
        )
        .filter(
            FormVersion.form_id == form_id
        )
    )

    # =====================================================
    # 5. APPLY FORM VERSION FILTER
    # =====================================================

    if form_version_id is not None:

        submission_query = submission_query.filter(
            Submission.form_version_id == form_version_id
        )

    # =====================================================
    # 6. APPLY START DATE FILTER
    # =====================================================

    if start_date is not None:

        start_datetime = datetime.combine(
            start_date,
            datetime.min.time()
        )

        submission_query = submission_query.filter(
            Submission.submitted_at >= start_datetime
        )

    # =====================================================
    # 7. APPLY END DATE FILTER
    # =====================================================

    if end_date is not None:

        end_datetime = (
            datetime.combine(
                end_date,
                datetime.min.time()
            )
            + timedelta(days=1)
        )

        submission_query = submission_query.filter(
            Submission.submitted_at < end_datetime
        )

    # =====================================================
    # 8. EXECUTE SUBMISSION QUERY
    # =====================================================

    submissions = submission_query.all()

    # =====================================================
    # 9. TOTAL SUBMISSIONS
    # =====================================================

    total_submissions = len(
        submissions
    )

    # =====================================================
    # 10. GET FORM STARTS
    # =====================================================

    form_start_query = (
        db.query(FormStart)
        .join(
            FormVersion,
            FormStart.form_version_id == FormVersion.id
        )
        .filter(
            FormVersion.form_id == form_id
        )
    )

    # =====================================================
    # 11. APPLY FORM VERSION FILTER TO STARTS
    # =====================================================

    if form_version_id is not None:

        form_start_query = form_start_query.filter(
            FormStart.form_version_id == form_version_id
        )

    # =====================================================
    # 12. APPLY START DATE FILTER TO FORM STARTS
    # =====================================================

    if start_date is not None:

        start_datetime = datetime.combine(
            start_date,
            datetime.min.time()
        )

        form_start_query = form_start_query.filter(
            FormStart.started_at >= start_datetime
        )

    # =====================================================
    # 13. APPLY END DATE FILTER TO FORM STARTS
    # =====================================================

    if end_date is not None:

        end_datetime = (
            datetime.combine(
                end_date,
                datetime.min.time()
            )
            + timedelta(days=1)
        )

        form_start_query = form_start_query.filter(
            FormStart.started_at < end_datetime
        )

    # =====================================================
    # 14. COUNT STARTED FORMS
    # =====================================================

    form_starts = form_start_query.count()

    # =====================================================
    # 15. STARTED FORMS
    # =====================================================

    started_forms = max(
        form_starts,
        total_submissions
    )

    # =====================================================
    # 16. COMPLETION RATE
    # =====================================================

    if started_forms > 0:

        completion_rate = (
            total_submissions /
            started_forms
        ) * 100

        completion_rate = round(
            completion_rate,
            2
        )

    else:

        completion_rate = 0

    # =====================================================
    # 17. COMPLETION TIMES
    # =====================================================

    completion_times = [

        submission.completion_time_seconds

        for submission in submissions

        if (
            submission.completion_time_seconds
            is not None
            and
            submission.completion_time_seconds > 0
        )

    ]

    # =====================================================
    # 18. AVERAGE COMPLETION TIME
    # =====================================================

    if completion_times:

        average_completion_time_seconds = (

            sum(completion_times) /
            len(completion_times)

        )

        average_completion_time_seconds = round(
            average_completion_time_seconds,
            2
        )

    else:

        average_completion_time_seconds = 0

    # =====================================================
    # 19. CONVERT TIME
    # =====================================================

    average_minutes = int(
        average_completion_time_seconds // 60
    )

    average_seconds = int(
        average_completion_time_seconds % 60
    )

    # =====================================================
    # 20. FIELD ANALYTICS
    # =====================================================

    field_analytics = []

    # =====================================================
    # 21. GET FIELDS
    # =====================================================

    fields_query = (
        db.query(Field)
        .join(
            FormVersion,
            Field.form_version_id == FormVersion.id
        )
        .filter(
            FormVersion.form_id == form_id
        )
    )

    # =====================================================
    # 22. APPLY FORM VERSION FILTER TO FIELDS
    # =====================================================

    if form_version_id is not None:

        fields_query = fields_query.filter(
            Field.form_version_id == form_version_id
        )

    fields = (
        fields_query
        .order_by(
            Field.display_order
        )
        .all()
    )

    # =====================================================
    # 23. GROUP FIELDS
    #
    # When "All Versions" is selected, fields having the
    # same label and field type are combined.
    #
    # Example:
    #
    # Version 1 -> Gender
    # Version 2 -> Gender
    # Version 3 -> Gender
    #
    # Result:
    #
    # One Gender analytics section.
    #
    # When a specific version is selected, the fields remain
    # separate because only one version is being analyzed.
    # =====================================================

    field_groups = OrderedDict()

    for field in fields:

        field_label = (
            field.label.strip()
            if field.label
            else "Untitled Field"
        )

        field_type = field.field_type

        # -------------------------------------------------
        # SPECIFIC VERSION
        # -------------------------------------------------

        if form_version_id is not None:

            group_key = (
                str(field.id),
                field_type
            )

        # -------------------------------------------------
        # ALL VERSIONS
        # -------------------------------------------------

        else:

            group_key = (
                field_label.lower(),
                field_type
            )

        if group_key not in field_groups:

            field_groups[group_key] = {
                "field_label": field_label,
                "field_type": field_type,
                "field_ids": [],
                "fields": []
            }

        field_groups[group_key]["field_ids"].append(
            field.id
        )

        field_groups[group_key]["fields"].append(
            field
        )

    # =====================================================
    # 24. ANALYZE EACH FIELD GROUP
    # =====================================================

    for group in field_groups.values():

        field_label = group["field_label"]
        field_type = group["field_type"]
        field_ids = group["field_ids"]
        grouped_fields = group["fields"]

        # -------------------------------------------------
        # ONLY DROPDOWN AND RATING
        # -------------------------------------------------

        if field_type not in [
            "dropdown",
            "rating"
        ]:

            continue

        # =================================================
        # GET RESPONSES FOR ALL FIELDS IN THIS GROUP
        # =================================================

        response_query = (
            db.query(ResponseValue)
            .join(
                Submission,
                ResponseValue.submission_id ==
                Submission.id
            )
            .join(
                FormVersion,
                Submission.form_version_id ==
                FormVersion.id
            )
            .filter(
                FormVersion.form_id == form_id,
                ResponseValue.field_id.in_(field_ids)
            )
        )

        # =================================================
        # APPLY FORM VERSION FILTER
        # =================================================

        if form_version_id is not None:

            response_query = response_query.filter(
                Submission.form_version_id ==
                form_version_id
            )

        # =================================================
        # APPLY START DATE FILTER
        # =================================================

        if start_date is not None:

            start_datetime = datetime.combine(
                start_date,
                datetime.min.time()
            )

            response_query = response_query.filter(
                Submission.submitted_at >= start_datetime
            )

        # =================================================
        # APPLY END DATE FILTER
        # =================================================

        if end_date is not None:

            end_datetime = (
                datetime.combine(
                    end_date,
                    datetime.min.time()
                )
                + timedelta(days=1)
            )

            response_query = response_query.filter(
                Submission.submitted_at < end_datetime
            )

        # =================================================
        # GET RESPONSE VALUES
        # =================================================

        response_values = response_query.all()

        # =================================================
        # COUNT ANSWERS
        # =================================================

        answer_counter = Counter()

        for response in response_values:

            if response.value is None:
                continue

            answer = response.value.strip()

            if answer == "":
                continue

            answer_counter[answer] += 1

        # =================================================
        # DROPDOWN ANALYTICS
        # =================================================

        if field_type == "dropdown":

            # -------------------------------------------------
            # COMBINE OPTIONS FROM ALL VERSIONS
            # -------------------------------------------------

            option_map = OrderedDict()

            for grouped_field in grouped_fields:

                options = (
                    db.query(FieldOption)
                    .filter(
                        FieldOption.field_id ==
                        grouped_field.id
                    )
                    .order_by(
                        FieldOption.display_order
                    )
                    .all()
                )

                for option in options:

                    option_key = (
                        option.option_value
                        if option.option_value
                        else option.option_label
                    )

                    if option_key not in option_map:

                        option_map[option_key] = {
                            "option":
                                option.option_label,

                            "value":
                                option.option_value,

                            "count": 0
                        }

            # -------------------------------------------------
            # CALCULATE COUNTS
            # -------------------------------------------------

            distribution = []

            for option_key, option_data in option_map.items():

                option_value = option_data["value"]
                option_label = option_data["option"]

                count = 0

                # First try option value.
                if option_value:

                    count = answer_counter.get(
                        option_value,
                        0
                    )

                # If not found, try option label.
                if count == 0 and option_label:

                    count = answer_counter.get(
                        option_label,
                        0
                    )

                distribution.append({

                    "option":
                        option_label,

                    "value":
                        option_value,

                    "count":
                        count

                })

            # -------------------------------------------------
            # RETURN ONE DROPDOWN ANALYTICS OBJECT
            # -------------------------------------------------

            field_analytics.append({

                "field_id":
                    str(grouped_fields[0].id),

                "field_label":
                    field_label,

                "field_type":
                    "dropdown",

                "distribution":
                    distribution

            })

        # =================================================
        # RATING ANALYTICS
        # =================================================

        elif field_type == "rating":

            distribution = []

            for rating in range(1, 6):

                count = answer_counter.get(
                    str(rating),
                    0
                )

                distribution.append({

                    "rating":
                        rating,

                    "count":
                        count

                })

            # -------------------------------------------------
            # RETURN ONE RATING ANALYTICS OBJECT
            # -------------------------------------------------

            field_analytics.append({

                "field_id":
                    str(grouped_fields[0].id),

                "field_label":
                    field_label,

                "field_type":
                    "rating",

                "distribution":
                    distribution

            })

    # =====================================================
    # 25. RETURN COMPLETE ANALYTICS
    # =====================================================

    return {

        "form_id":
            str(form.id),

        "form_title":
            form.title,

        "total_submissions":
            total_submissions,

        "started_forms":
            started_forms,

        "completion_rate":
            completion_rate,

        "completion_rate_percentage":
            f"{completion_rate}%",

        "average_completion_time_seconds":
            average_completion_time_seconds,

        "average_completion_time":
            f"{average_minutes} min "
            f"{average_seconds} sec",

        "field_analytics":
            field_analytics,

        # =================================================
        # FILTER INFORMATION
        # =================================================

        "filters": {

            "start_date":
                str(start_date)
                if start_date
                else None,

            "end_date":
                str(end_date)
                if end_date
                else None,

            "form_version_id":
                str(form_version_id)
                if form_version_id
                else None

        }

    }