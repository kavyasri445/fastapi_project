import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.uploaded_file import UploadedFile


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    tags=["File Upload"]
)


# =========================================================
# CONFIGURATION
# =========================================================

UPLOAD_DIR = Path("uploads")

# Create uploads folder if it does not exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".jpg",
    ".jpeg",
    ".png",
}


# =========================================================
# UPLOAD FILE
# POST /upload
# =========================================================

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # 1. CHECK FILE NAME
    # -----------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is required"
        )

    # -----------------------------------------------------
    # 2. CHECK FILE EXTENSION
    # -----------------------------------------------------

    original_name = file.filename

    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid file type. Allowed types: "
                "pdf, doc, docx, jpg, jpeg, png"
            )
        )

    # -----------------------------------------------------
    # 3. READ FILE
    # -----------------------------------------------------

    file_content = await file.read()

    # -----------------------------------------------------
    # 4. CHECK FILE SIZE
    # -----------------------------------------------------

    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size must not exceed 5 MB"
        )

    # -----------------------------------------------------
    # 5. GENERATE UNIQUE FILE NAME
    # -----------------------------------------------------

    unique_name = f"{uuid.uuid4().hex}_{original_name}"

    file_path = UPLOAD_DIR / unique_name

    # -----------------------------------------------------
    # 6. SAVE FILE TO LOCAL STORAGE
    # -----------------------------------------------------

    try:

        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    # -----------------------------------------------------
    # 7. SAVE FILE METADATA TO DATABASE
    # -----------------------------------------------------

    uploaded_file = UploadedFile(
        original_name=original_name,
        stored_name=unique_name,
        file_path=str(file_path),
        file_size=file_size
    )

    db.add(uploaded_file)

    try:

        db.commit()
        db.refresh(uploaded_file)

    except Exception as e:

        db.rollback()

        # Remove saved file if database insertion fails
        if file_path.exists():
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file metadata: {str(e)}"
        )

    # -----------------------------------------------------
    # 8. SUCCESS RESPONSE
    # -----------------------------------------------------

    return {
        "message": "File uploaded successfully",
        "file_id": str(uploaded_file.id),
        "original_name": uploaded_file.original_name,
        "stored_name": uploaded_file.stored_name,
        "file_size": uploaded_file.file_size
    }