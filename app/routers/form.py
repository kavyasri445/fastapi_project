import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.form import Form
from app.models.form_version import FormVersion
from app.models.field import Field
from app.models.public_link import PublicLink

from app.schemas.form import (
    FormCreate,
    FormResponse,
    FormUpdate
)

router = APIRouter(
    prefix="/forms",
    tags=["Forms"]
)


# =========================================================
# 1. CREATE FORM
# POST /forms/
# =========================================================

@router.post("/", response_model=FormResponse)
def create_form(
    form: FormCreate,
    db: Session = Depends(get_db)
):
    new_form = Form(
        title=form.title,
        description=form.description,
        status="draft",
        created_by=form.created_by
    )

    db.add(new_form)
    db.flush()

    # Create first DRAFT version
    new_version = FormVersion(
        form_id=new_form.id,
        version_number=1,
        is_active=False,
        published_at=None
    )

    db.add(new_version)

    db.commit()
    db.refresh(new_form)

    return new_form


# =========================================================
# 2. GET ALL FORMS
# GET /forms/
# =========================================================

@router.get("/", response_model=list[FormResponse])
def get_forms(
    db: Session = Depends(get_db)
):
    return db.query(Form).all()


# =========================================================
# 3. GET FORM BY ID
# GET /forms/{form_id}
# =========================================================

@router.get("/{form_id}")
def get_form(
    form_id: str,
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    versions = db.query(FormVersion).filter(
        FormVersion.form_id == form.id
    ).order_by(
        FormVersion.version_number
    ).all()

    result = {
        "id": str(form.id),
        "title": form.title,
        "description": form.description,
        "status": form.status,
        "created_by": str(form.created_by),
        "created_at": form.created_at,
        "updated_at": form.updated_at,
        "versions": []
    }

    for version in versions:

        fields = db.query(Field).filter(
            Field.form_version_id == version.id
        ).order_by(
            Field.display_order
        ).all()

        result["versions"].append({
            "id": str(version.id),
            "version_number": version.version_number,
            "is_active": version.is_active,
            "published_at": version.published_at,
            "fields": [
                {
                    "id": str(field.id),
                    "label": field.label,
                    "field_type": field.field_type,
                    "placeholder": field.placeholder,
                    "is_required": field.is_required,
                    "display_order": field.display_order,
                    "validation_config": field.validation_config
                }
                for field in fields
            ]
        })

    return result


# =========================================================
# 4. UPDATE FORM
# PUT /forms/{form_id}
# =========================================================

@router.put("/{form_id}", response_model=FormResponse)
def update_form(
    form_id: str,
    form_data: FormUpdate,
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    if form.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft forms can be updated"
        )

    if form_data.title is not None:
        form.title = form_data.title

    if form_data.description is not None:
        form.description = form_data.description

    db.commit()
    db.refresh(form)

    return form


# =========================================================
# 5. ARCHIVE FORM
# PATCH /forms/{form_id}/archive
# =========================================================

@router.patch("/{form_id}/archive")
def archive_form(
    form_id: str,
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    if form.status == "archived":
        raise HTTPException(
            status_code=400,
            detail="Form is already archived"
        )

    form.status = "archived"

    db.commit()
    db.refresh(form)

    return {
        "message": "Form archived successfully",
        "form_id": str(form.id),
        "status": form.status
    }


# =========================================================
# 6. ADD FIELD
# POST /forms/{form_id}/fields
# =========================================================

@router.post("/{form_id}/fields")
def add_field_to_form(
    form_id: str,
    field_data: dict,
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    if form.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Fields can only be added to draft forms"
        )

    # Latest draft version
    draft_version = db.query(FormVersion).filter(
        FormVersion.form_id == form.id,
        FormVersion.is_active == False
    ).order_by(
        FormVersion.version_number.desc()
    ).first()

    if not draft_version:
        raise HTTPException(
            status_code=404,
            detail="Draft form version not found"
        )

    new_field = Field(
        form_version_id=draft_version.id,
        label=field_data["label"],
        field_type=field_data["field_type"],
        placeholder=field_data.get("placeholder"),
        is_required=field_data.get("is_required", False),
        display_order=field_data.get("display_order", 1),
        validation_config=field_data.get("validation_config", {})
    )

    db.add(new_field)
    db.commit()
    db.refresh(new_field)

    return {
        "id": str(new_field.id),
        "form_version_id": str(new_field.form_version_id),
        "label": new_field.label,
        "field_type": new_field.field_type,
        "placeholder": new_field.placeholder,
        "is_required": new_field.is_required,
        "display_order": new_field.display_order,
        "validation_config": new_field.validation_config
    }


# =========================================================
# 7. DELETE FIELD
# DELETE /forms/fields/{field_id}
# =========================================================

@router.delete("/fields/{field_id}")
def remove_field(
    field_id: str,
    db: Session = Depends(get_db)
):
    field = db.query(Field).filter(
        Field.id == field_id
    ).first()

    if not field:
        raise HTTPException(
            status_code=404,
            detail="Field not found"
        )

    version = db.query(FormVersion).filter(
        FormVersion.id == field.form_version_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Form version not found"
        )

    form = db.query(Form).filter(
        Form.id == version.form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    if form.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Fields can only be removed from draft forms"
        )

    db.delete(field)
    db.commit()

    return {
        "message": "Field deleted successfully",
        "field_id": field_id
    }


# =========================================================
# 8. REORDER FIELDS
# PATCH /forms/{form_id}/reorder-fields
# =========================================================

@router.patch("/{form_id}/reorder-fields")
def reorder_fields(
    form_id: str,
    field_order: list[str],
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    if form.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Fields can only be reordered in draft forms"
        )

    draft_version = db.query(FormVersion).filter(
        FormVersion.form_id == form.id,
        FormVersion.is_active == False
    ).order_by(
        FormVersion.version_number.desc()
    ).first()

    if not draft_version:
        raise HTTPException(
            status_code=404,
            detail="Draft form version not found"
        )

    for order, field_id in enumerate(field_order, start=1):

        field = db.query(Field).filter(
            Field.id == field_id,
            Field.form_version_id == draft_version.id
        ).first()

        if not field:
            raise HTTPException(
                status_code=404,
                detail=f"Field {field_id} not found in draft version"
            )

        field.display_order = order

    db.commit()

    fields = db.query(Field).filter(
        Field.form_version_id == draft_version.id
    ).order_by(
        Field.display_order
    ).all()

    return {
        "form_id": str(form.id),
        "version_id": str(draft_version.id),
        "fields": [
            {
                "id": str(field.id),
                "label": field.label,
                "field_type": field.field_type,
                "display_order": field.display_order
            }
            for field in fields
        ]
    }


# =========================================================
# 9. PUBLISH FORM
# POST /forms/{form_id}/publish
# =========================================================

@router.post("/{form_id}/publish")
def publish_form(
    form_id: str,
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    if form.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft forms can be published"
        )

    # Find latest draft version
    draft_version = db.query(FormVersion).filter(
        FormVersion.form_id == form.id,
        FormVersion.is_active == False
    ).order_by(
        FormVersion.version_number.desc()
    ).first()

    if not draft_version:
        raise HTTPException(
            status_code=404,
            detail="Draft version not found"
        )

    # Deactivate previous active versions
    db.query(FormVersion).filter(
        FormVersion.form_id == form.id,
        FormVersion.is_active == True
    ).update(
        {
            FormVersion.is_active: False
        }
    )

    # Publish draft version
    draft_version.is_active = True
    draft_version.published_at = datetime.utcnow()

    form.status = "published"

    db.commit()
    db.refresh(form)
    db.refresh(draft_version)

    return {
        "message": "Form published successfully",
        "form_id": str(form.id),
        "version_id": str(draft_version.id),
        "version_number": draft_version.version_number,
        "status": form.status,
        "published_at": draft_version.published_at
    }


# =========================================================
# 10. VERSION HISTORY
# GET /forms/{form_id}/versions
# =========================================================

@router.get("/{form_id}/versions")
def get_version_history(
    form_id: str,
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    versions = db.query(FormVersion).filter(
        FormVersion.form_id == form.id
    ).order_by(
        FormVersion.version_number
    ).all()

    return {
        "form_id": str(form.id),
        "form_title": form.title,
        "current_status": form.status,
        "versions": [
            {
                "version_id": str(version.id),
                "version_number": version.version_number,
                "is_active": version.is_active,
                "published_at": version.published_at
            }
            for version in versions
        ]
    }


# =========================================================
# 11. CREATE NEW VERSION
# POST /forms/{form_id}/new-version
# =========================================================

@router.post("/{form_id}/new-version")
def create_new_version(
    form_id: str,
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    if form.status != "published":
        raise HTTPException(
            status_code=400,
            detail="Only published forms can create a new version"
        )

    # Current published version
    old_version = db.query(FormVersion).filter(
        FormVersion.form_id == form.id,
        FormVersion.is_active == True
    ).first()

    if not old_version:
        raise HTTPException(
            status_code=404,
            detail="Active version not found"
        )

    old_fields = db.query(Field).filter(
        Field.form_version_id == old_version.id
    ).order_by(
        Field.display_order
    ).all()

    latest_version = db.query(FormVersion).filter(
        FormVersion.form_id == form.id
    ).order_by(
        FormVersion.version_number.desc()
    ).first()

    new_version = FormVersion(
        form_id=form.id,
        version_number=latest_version.version_number + 1,
        is_active=False,
        published_at=None
    )

    db.add(new_version)
    db.flush()

    # Copy fields
    for old_field in old_fields:

        new_field = Field(
            form_version_id=new_version.id,
            label=old_field.label,
            field_type=old_field.field_type,
            placeholder=old_field.placeholder,
            is_required=old_field.is_required,
            display_order=old_field.display_order,
            validation_config=old_field.validation_config
        )

        db.add(new_field)

    form.status = "draft"

    db.commit()
    db.refresh(new_version)

    return {
        "message": "New draft version created successfully",
        "form_id": str(form.id),
        "version_id": str(new_version.id),
        "version_number": new_version.version_number,
        "status": form.status
    }


# =========================================================
# 12. VERSION DETAILS
# GET /forms/{form_id}/versions/{version_id}
# =========================================================

@router.get("/{form_id}/versions/{version_id}")
def get_version_details(
    form_id: str,
    version_id: str,
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    version = db.query(FormVersion).filter(
        FormVersion.id == version_id,
        FormVersion.form_id == form.id
    ).first()

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Version not found"
        )

    fields = db.query(Field).filter(
        Field.form_version_id == version.id
    ).order_by(
        Field.display_order
    ).all()

    return {
        "form_id": str(form.id),
        "form_title": form.title,
        "version_id": str(version.id),
        "version_number": version.version_number,
        "is_active": version.is_active,
        "published_at": version.published_at,
        "status": "published" if version.published_at else "draft",
        "fields": [
            {
                "id": str(field.id),
                "label": field.label,
                "field_type": field.field_type,
                "placeholder": field.placeholder,
                "is_required": field.is_required,
                "display_order": field.display_order,
                "validation_config": field.validation_config
            }
            for field in fields
        ]
    }


# =========================================================
# 13. GENERATE PUBLIC FORM LINK
# POST /forms/{form_id}/generate-link
# =========================================================

@router.post("/{form_id}/generate-link")
def generate_public_link(
    form_id: str,
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    if form.status != "published":
        raise HTTPException(
            status_code=400,
            detail="Only published forms can generate a public link"
        )

    active_version = db.query(FormVersion).filter(
        FormVersion.form_id == form.id,
        FormVersion.is_active == True
    ).first()

    if not active_version:
        raise HTTPException(
            status_code=404,
            detail="Published version not found"
        )

    existing_link = db.query(PublicLink).filter(
        PublicLink.form_id == form.id,
        PublicLink.form_version_id == active_version.id,
        PublicLink.is_active == True
    ).first()

    if existing_link:
        slug = existing_link.slug

    else:
        while True:

            slug = secrets.token_urlsafe(16)

            existing_slug = db.query(PublicLink).filter(
                PublicLink.slug == slug
            ).first()

            if not existing_slug:
                break

        new_link = PublicLink(
            form_id=form.id,
            form_version_id=active_version.id,
            slug=slug,
            is_active=True
        )

        db.add(new_link)
        db.commit()
        db.refresh(new_link)

    public_url = (
        f"http://127.0.0.1:8000/public/forms/{slug}"
    )

    return {
        "message": "Public form link generated successfully",
        "form_id": str(form.id),
        "version_id": str(active_version.id),
        "version_number": active_version.version_number,
        "slug": slug,
        "public_url": public_url
    }