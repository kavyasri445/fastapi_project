from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.uploaded_file import UploadedFile
from app.services.auth import get_current_admin


router = APIRouter(
    prefix="/admin/files",
    tags=["Admin Files"]
)


# =========================================================
# GET ALL UPLOADED FILES
# GET /admin/files
# =========================================================

@router.get("/")
def get_uploaded_files(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    files = (
        db.query(UploadedFile)
        .order_by(
            UploadedFile.uploaded_at.desc()
        )
        .all()
    )

    return [
        {
            "file_id": str(uploaded_file.id),
            "original_name": uploaded_file.original_name,
            "stored_name": uploaded_file.stored_name,
            "file_path": uploaded_file.file_path,
            "file_size": uploaded_file.file_size,
            "uploaded_at": uploaded_file.uploaded_at
        }
        for uploaded_file in files
    ]