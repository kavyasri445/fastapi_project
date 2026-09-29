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
# 1. CREATE FIELD
# POST /fields/
# =========================================================

@router.post("/")
def create_field(
    field_data: dict,
    db: Session = Depends(get_db)
):
    # Get values from request
    form_id = field_data.get("form_id")
    label = field_data.get("label")
    field_type = field_data.get("field_type")

    # Validate required values
    if not form_id:
        raise HTTPException(
            status_code=400,
            detail="form_id is required"
        )

    if not label:
        raise HTTPException(
            status_code=400,
            detail="Field label is required"
        )

    if not field_type:
        raise HTTPException(
            status_code=400,
            detail="field_type is required"
        )

    # Find form
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    # Only draft forms can be modified
    if form.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Fields can only be added to draft forms"
        )

    # Find latest draft version
    form_version = db.query(FormVersion).filter(
        FormVersion.form_id == form.id,
        FormVersion.is_active == False
    ).order_by(
        FormVersion.version_number.desc()
    ).first()

    if not form_version:
        raise HTTPException(
            status_code=404,
            detail="No draft form version found"
        )

    # Find current highest display order
    last_field = db.query(Field).filter(
        Field.form_version_id == form_version.id
    ).order_by(
        Field.display_order.desc()
    ).first()

    if last_field:
        next_order = last_field.display_order + 1
    else:
        next_order = 1

    # Create new field
    new_field = Field(
        form_version_id=form_version.id,
        label=label,
        field_type=field_type,
        placeholder=field_data.get("placeholder"),
        is_required=field_data.get("is_required", False),
        display_order=next_order,
        validation_config=field_data.get("validation_config")
    )

    db.add(new_field)
    db.commit()
    db.refresh(new_field)

    return {
        "message": "Field created successfully",
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
# 2. GET ALL FIELDS FOR A FORM
# GET /fields/form/{form_id}
# =========================================================

@router.get("/form/{form_id}")
def get_fields_for_form(
    form_id: str,
    db: Session = Depends(get_db)
):
    # Find form
    form = db.query(Form).filter(
        Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    # First try to get active version
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
            detail="No form version found"
        )

    # Get fields
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
# 3. UPDATE FIELD
# PUT /fields/{field_id}
# =========================================================

@router.put("/{field_id}")
def update_field(
    field_id: str,
    field_data: dict,
    db: Session = Depends(get_db)
):
    # Find field
    field = db.query(Field).filter(
        Field.id == field_id
    ).first()

    if not field:
        raise HTTPException(
            status_code=404,
            detail="Field not found"
        )

    # Find form version
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

    # Cannot update active version
    if form_version.is_active:
        raise HTTPException(
            status_code=400,
            detail="Published version cannot be modified"
        )

    # Only draft forms can be modified
    if form.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Fields can only be updated in draft forms"
        )

    # Update values if provided
    if "label" in field_data:
        field.label = field_data["label"]

    if "placeholder" in field_data:
        field.placeholder = field_data["placeholder"]

    if "is_required" in field_data:
        field.is_required = field_data["is_required"]

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
# 4. DELETE FIELD
# DELETE /fields/{field_id}
# =========================================================

@router.delete("/{field_id}")
def delete_field(
    field_id: str,
    db: Session = Depends(get_db)
):
    # Find field
    field = db.query(Field).filter(
        Field.id == field_id
    ).first()

    if not field:
        raise HTTPException(
            status_code=404,
            detail="Field not found"
        )

    # Find form version
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

    # Cannot delete from active version
    if form_version.is_active:
        raise HTTPException(
            status_code=400,
            detail="Published version cannot be modified"
        )

    # Only draft forms can be modified
    if form.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Fields can only be deleted from draft forms"
        )

    # Delete field
    db.delete(field)
    db.commit()

    return {
        "message": "Field deleted successfully"
    }


# =========================================================
# 5. REORDER FIELD
# PUT /fields/{field_id}/reorder
# =========================================================

@router.put("/{field_id}/reorder")
def reorder_field(
    field_id: str,
    new_order: int,
    db: Session = Depends(get_db)
):
    # Validate order
    if new_order < 1:
        raise HTTPException(
            status_code=400,
            detail="new_order must be greater than or equal to 1"
        )

    # Find field
    field = db.query(Field).filter(
        Field.id == field_id
    ).first()

    if not field:
        raise HTTPException(
            status_code=404,
            detail="Field not found"
        )

    # Find form version
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

    # Cannot reorder active version
    if form_version.is_active:
        raise HTTPException(
            status_code=400,
            detail="Published version cannot be modified"
        )

    # Only draft forms can be modified
    if form.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Fields can only be reordered in draft forms"
        )

    # Update display order
    field.display_order = new_order

    db.commit()
    db.refresh(field)

    return {
        "message": "Field reordered successfully",
        "id": str(field.id),
        "display_order": field.display_order
    }