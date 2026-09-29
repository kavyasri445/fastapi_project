from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.form import Form
from app.models.form_version import FormVersion
from app.schemas.form_version import FormVersionCreate, FormVersionResponse


router = APIRouter(
    prefix="/form-versions",
    tags=["Form Versions"]
)


# =========================================================
# 1. CREATE FORM VERSION
# POST /form-versions/
# =========================================================

@router.post("/", response_model=FormVersionResponse)
def create_form_version(
    form_version: FormVersionCreate,
    db: Session = Depends(get_db)
):
    # Check whether form exists
    form = db.query(Form).filter(
        Form.id == form_version.form_id
    ).first()

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    new_version = FormVersion(
        form_id=form_version.form_id,
        version_number=form_version.version_number,
        is_active=form_version.is_active
    )

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return new_version


# =========================================================
# 2. GET ALL FORM VERSIONS
# GET /form-versions/
# =========================================================

@router.get("/", response_model=list[FormVersionResponse])
def get_form_versions(
    db: Session = Depends(get_db)
):
    return db.query(FormVersion).all()


# =========================================================
# 3. PUBLISH FORM VERSION
# POST /form-versions/{version_id}/publish
# =========================================================

@router.post(
    "/{version_id}/publish",
    response_model=FormVersionResponse
)
def publish_form_version(
    version_id: str,
    db: Session = Depends(get_db)
):
    # Find form version
    version = (
        db.query(FormVersion)
        .filter(FormVersion.id == version_id)
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Form version not found"
        )

    # Find parent form
    form = (
        db.query(Form)
        .filter(Form.id == version.form_id)
        .first()
    )

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form not found"
        )

    # Deactivate other versions of the same form
    db.query(FormVersion).filter(
        FormVersion.form_id == version.form_id,
        FormVersion.id != version.id
    ).update(
        {
            FormVersion.is_active: False
        },
        synchronize_session=False
    )

    # Publish selected version
    version.is_active = True
    version.published_at = datetime.utcnow()

    # IMPORTANT:
    # Update parent form status
    form.status = "published"

    db.commit()

    db.refresh(version)
    db.refresh(form)

    return version