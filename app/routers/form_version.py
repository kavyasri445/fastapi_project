from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.form_version import FormVersion
from app.schemas.form_version import FormVersionCreate, FormVersionResponse


router = APIRouter(
    prefix="/form-versions",
    tags=["Form Versions"]
)


@router.post("/", response_model=FormVersionResponse)
def create_form_version(
    form_version: FormVersionCreate,
    db: Session = Depends(get_db)
):
    new_version = FormVersion(
        form_id=form_version.form_id,
        version_number=form_version.version_number,
        is_active=form_version.is_active
    )

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return new_version


@router.get("/", response_model=list[FormVersionResponse])
def get_form_versions(
    db: Session = Depends(get_db)
):
    return db.query(FormVersion).all()


@router.post(
    "/{version_id}/publish",
    response_model=FormVersionResponse
)
def publish_form_version(
    version_id: str,
    db: Session = Depends(get_db)
):
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

    # Deactivate other versions of the same form
    db.query(FormVersion).filter(
        FormVersion.form_id == version.form_id
    ).update(
        {
            FormVersion.is_active: False
        }
    )

    # Publish selected version
    version.is_active = True
    version.published_at = datetime.utcnow()

    db.commit()
    db.refresh(version)

    return version