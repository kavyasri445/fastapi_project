from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.form import Form
from app.models.form_version import FormVersion
from app.models.field import Field
from app.models.field_option import FieldOption
from app.models.public_link import PublicLink
from app.models.conditional_rule import ConditionalRule


router = APIRouter(
    prefix="/public",
    tags=["Public Forms"]
)


# =========================================================
# TEMPLATE DIRECTORY
# =========================================================

# public_form.py is inside:
# fastapi_project/app/routers/
#
# parent.parent.parent -> fastapi_project

BASE_DIR = Path(__file__).resolve().parent.parent.parent

TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


# =========================================================
# DISPLAY PUBLIC FORM PAGE
# GET /public/form-page/{slug}
# =========================================================

@router.get("/form-page/{slug}")
def public_form_page(
    slug: str,
    request: Request
):
    print("===================================")
    print("PUBLIC FORM PAGE CALLED")
    print("Slug:", slug)
    print("Template directory:", TEMPLATES_DIR)
    print(
        "Template directory exists:",
        TEMPLATES_DIR.exists()
    )
    print(
        "HTML file exists:",
        (TEMPLATES_DIR / "public_form.html").exists()
    )
    print("===================================")

    return templates.TemplateResponse(
        request=request,
        name="public_form.html"
    )


# =========================================================
# GET PUBLIC FORM DATA
# GET /public/forms/{slug}
# =========================================================

@router.get("/forms/{slug}")
def get_public_form(
    slug: str,
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # 1. Find public link
    # -----------------------------------------------------

    public_link = db.query(PublicLink).filter(
        PublicLink.slug == slug,
        PublicLink.is_active == True
    ).first()

    if not public_link:
        raise HTTPException(
            status_code=404,
            detail="Invalid or expired public link"
        )

    # -----------------------------------------------------
    # 2. Find form
    # -----------------------------------------------------

    form = db.query(Form).filter(
        Form.id == public_link.form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    # -----------------------------------------------------
    # 3. Check form status
    # -----------------------------------------------------

    if form.status == "archived":
        raise HTTPException(
            status_code=410,
            detail="This form has been archived"
        )

    if form.status != "published":
        raise HTTPException(
            status_code=404,
            detail="This form is currently unavailable"
        )

    # -----------------------------------------------------
    # 4. Find published version
    # -----------------------------------------------------

    version = db.query(FormVersion).filter(
        FormVersion.id == public_link.form_version_id,
        FormVersion.form_id == form.id
    ).first()

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Published form version not found"
        )

    # -----------------------------------------------------
    # 5. Check version is published
    # -----------------------------------------------------

    if not version.is_active or version.published_at is None:
        raise HTTPException(
            status_code=404,
            detail="This form version is no longer available"
        )

    # -----------------------------------------------------
    # 6. Get fields
    # -----------------------------------------------------

    fields = db.query(Field).filter(
        Field.form_version_id == version.id
    ).order_by(
        Field.display_order
    ).all()

    # -----------------------------------------------------
    # 7. Get conditional rules
    # -----------------------------------------------------

    rules = db.query(ConditionalRule).filter(
        ConditionalRule.form_id == form.id
    ).all()

    # -----------------------------------------------------
    # 8. Return public form information
    # -----------------------------------------------------

    return {
        "form_id": str(form.id),
        "title": form.title,
        "description": form.description,

        "version_id": str(version.id),
        "version_number": version.version_number,
        "published_at": version.published_at,

        "fields": [
            {
                "id": str(field.id),
                "label": field.label,
                "field_type": field.field_type,
                "placeholder": field.placeholder,
                "is_required": field.is_required,
                "display_order": field.display_order,
                "validation_config": field.validation_config,

                # -------------------------------------------------
                # FIELD OPTIONS
                # -------------------------------------------------
                "options": [
                    {
                        "id": str(option.id),
                        "label": option.option_label,
                        "value": option.option_value,
                        "display_order": option.display_order
                    }
                    for option in db.query(FieldOption).filter(
                        FieldOption.field_id == field.id
                    ).order_by(
                        FieldOption.display_order
                    ).all()
                ]
            }
            for field in fields
        ],

        "conditional_rules": [
            {
                "id": str(rule.id),
                "trigger_field_id": str(rule.trigger_field_id),
                "operator": rule.operator,
                "comparison_value": rule.comparison_value,
                "target_field_id": str(rule.target_field_id),
                "action": rule.action
            }
            for rule in rules
        ]
    }