from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.field import Field
from app.models.form import Form
from app.models.form_version import FormVersion


router = APIRouter(
    prefix="/fields",
    tags=["Fields"]
)


# =========================================================
# 1. GET FIELDS FOR A FORM
# GET /fields/form/{form_id}
# =========================================================

@router.get("/form/{form_id}")
def get_fields_for_form(
    form_id: str,
    db: Session = Depends(get_db)
):
    # Check form
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    # Get active version
    active_version = db.query(FormVersion).filter(
        FormVersion.form_id == form.id,
        FormVersion.is_active == True
    ).first()

    # If no active version, get latest version
    if not active_version:
        active_version = db.query(FormVersion).filter(
            FormVersion.form_id == form.id
        ).order_by(
            FormVersion.version_number.desc()
        ).first()

    if not active_version:
        raise HTTPException(
            status_code=404,
            detail="Form version not found"
        )

    fields = db.query(Field).filter(
        Field.form_version_id == active_version.id
    ).order_by(
        Field.display_order
    ).all()

    return [
        {
            "id": str(field.id),
            "form_version_id": str(field.form_version_id),
            "label": field.label,
            "field_type": field.field_type,
            "placeholder": field.placeholder,
            "is_required": field.is_required,
            "display_order": field.display_order,
            "validation_config": field.validation_config
        }
        for field in fields
    ]


# =========================================================
# 2. UPDATE FIELD
# PUT /fields/{field_id}
# =========================================================

@router.put("/{field_id}")
def update_field(
    field_id: str,
    field_data: dict,
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

    # Find version
    form_version = db.query(FormVersion).filter(
        FormVersion.id == field.form_version_id
    ).first()

    if not form_version:
        raise HTTPException(
            status_code=404,
            detail="Form version not found"
        )

    # Find form
    form = db.query(Form).filter(
        Form.id == form_version.form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    # Never modify published version
    if form_version.is_active:
        raise HTTPException(
            status_code=400,
            detail="Published version cannot be modified"
        )

    # Only draft forms can be modified
    if form.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft forms can be modified"
        )

    # Update label
    if "label" in field_data:
        field.label = field_data["label"]

    # Update placeholder
    if "placeholder" in field_data:
        field.placeholder = field_data["placeholder"]

    # Update required status
    if "is_required" in field_data:
        field.is_required = field_data["is_required"]

    # Update validation configuration
    if "validation_config" in field_data:
        field.validation_config = field_data["validation_config"]

    db.commit()
    db.refresh(field)

    return {
        "message": "Field updated successfully",
        "id": str(field.id),
        "form_version_id": str(field.form_version_id),
        "label": field.label,
        "field_type": field.field_type,
        "placeholder": field.placeholder,
        "is_required": field.is_required,
        "display_order": field.display_order,
        "validation_config": field.validation_config
    }


# =========================================================
# 3. DELETE FIELD
# DELETE /fields/{field_id}
# =========================================================

@router.delete("/{field_id}")
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

    form_version = db.query(FormVersion).filter(
        FormVersion.id == field.form_version_id
    ).first()

    if not form_version:
        raise HTTPException(
            status_code=404,
            detail="Form version not found"
        )

    form = db.query(Form).filter(
        Form.id == form_version.form_id
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

    # Do not modify published version
    if form_version.is_active:
        raise HTTPException(
            status_code=400,
            detail="Published version cannot be modified"
        )

    db.delete(field)
    db.commit()

    return {
        "message": "Field deleted successfully",
        "field_id": field_id
    }


# =========================================================
# 4. REORDER FIELD
# PUT /fields/{field_id}/reorder
# =========================================================

@router.put("/{field_id}/reorder")
def reorder_field(
    field_id: str,
    new_order: int,
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

    form_version = db.query(FormVersion).filter(
        FormVersion.id == field.form_version_id
    ).first()

    if not form_version:
        raise HTTPException(
            status_code=404,
            detail="Form version not found"
        )

    form = db.query(Form).filter(
        Form.id == form_version.form_id
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

    if form_version.is_active:
        raise HTTPException(
            status_code=400,
            detail="Published version cannot be modified"
        )

    if new_order < 1:
        raise HTTPException(
            status_code=400,
            detail="Order must be greater than 0"
        )

    field.display_order = new_order

    db.commit()
    db.refresh(field)

    return {
        "message": "Field reordered successfully",
        "field_id": str(field.id),
        "display_order": field.display_order
    }