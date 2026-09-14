import hmac
import hashlib
import base64
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.uploaded_file import UploadedFile
from app.config import settings


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/files",
    tags=["Files"]
)


# =========================================================
# CONFIGURATION
# =========================================================

UPLOAD_DIR = Path("uploads").resolve()

FILE_ACCESS_SECRET = settings.FILE_ACCESS_SECRET

TOKEN_EXPIRATION_SECONDS = 10 * 60


# =========================================================
# CREATE SECURE TOKEN
# =========================================================

def create_file_token(file_id: str) -> str:

    expires_at = int(time.time()) + TOKEN_EXPIRATION_SECONDS

    payload = f"{file_id}:{expires_at}"

    signature = hmac.new(
        FILE_ACCESS_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    token_data = f"{payload}:{signature}"

    token = base64.urlsafe_b64encode(
        token_data.encode()
    ).decode()

    return token


# =========================================================
# VERIFY SECURE TOKEN
# =========================================================

def verify_file_token(
    file_id: str,
    token: str
):

    try:

        decoded_token = base64.urlsafe_b64decode(
            token.encode()
        ).decode()

        parts = decoded_token.split(":")

        if len(parts) != 3:
            return False

        token_file_id = parts[0]
        expires_at = int(parts[1])
        received_signature = parts[2]

        # Check file ID
        if token_file_id != file_id:
            return False

        # Check expiration
        if int(time.time()) > expires_at:
            return False

        # Re-create signature
        payload = f"{token_file_id}:{expires_at}"

        expected_signature = hmac.new(
            FILE_ACCESS_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        # Secure comparison
        if not hmac.compare_digest(
            received_signature,
            expected_signature
        ):
            return False

        return True

    except Exception:
        return False


# =========================================================
# GENERATE SECURE DOWNLOAD URL
# GET /files/{file_id}/secure-url
# =========================================================

@router.get("/{file_id}/secure-url")
def generate_secure_file_url(
    file_id: str,
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # 1. FIND FILE
    # -----------------------------------------------------

    uploaded_file = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.id == file_id
        )
        .first()
    )

    if uploaded_file is None:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    # -----------------------------------------------------
    # 2. GET FILE PATH
    # -----------------------------------------------------

    file_path = Path(
        uploaded_file.file_path
    ).resolve()

    # -----------------------------------------------------
    # 3. CHECK PHYSICAL FILE
    # -----------------------------------------------------

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Physical file not found"
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Invalid file path"
        )

    # -----------------------------------------------------
    # 4. SECURITY CHECK
    # -----------------------------------------------------

    try:

        file_path.relative_to(UPLOAD_DIR)

    except ValueError:

        raise HTTPException(
            status_code=403,
            detail="Access to this file is not allowed"
        )

    # -----------------------------------------------------
    # 5. CREATE TOKEN
    # -----------------------------------------------------

    token = create_file_token(
        str(uploaded_file.id)
    )

    # -----------------------------------------------------
    # 6. CREATE SECURE URL
    # -----------------------------------------------------

    secure_url = (
        f"/files/{uploaded_file.id}"
        f"?token={token}"
    )

    return {
        "message": "Secure download URL generated",
        "file_id": str(uploaded_file.id),
        "expires_in_seconds": TOKEN_EXPIRATION_SECONDS,
        "download_url": secure_url
    }


# =========================================================
# DOWNLOAD FILE
# GET /files/{file_id}?token=...
# =========================================================

@router.get("/{file_id}")
def download_file(
    file_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # 1. VERIFY TOKEN
    # -----------------------------------------------------

    if not verify_file_token(
        file_id,
        token
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired file access token"
        )

    # -----------------------------------------------------
    # 2. FIND FILE
    # -----------------------------------------------------

    uploaded_file = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.id == file_id
        )
        .first()
    )

    if uploaded_file is None:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    # -----------------------------------------------------
    # 3. GET FILE PATH
    # -----------------------------------------------------

    file_path = Path(
        uploaded_file.file_path
    ).resolve()

    # -----------------------------------------------------
    # 4. CHECK PHYSICAL FILE
    # -----------------------------------------------------

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Physical file not found"
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Invalid file path"
        )

    # -----------------------------------------------------
    # 5. SECURITY CHECK
    # -----------------------------------------------------

    try:

        file_path.relative_to(UPLOAD_DIR)

    except ValueError:

        raise HTTPException(
            status_code=403,
            detail="Access to this file is not allowed"
        )

    # -----------------------------------------------------
    # 6. RETURN FILE
    # -----------------------------------------------------

    return FileResponse(
        path=str(file_path),
        filename=uploaded_file.original_name,
        media_type="application/octet-stream"
    )