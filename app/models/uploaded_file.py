import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    original_name = Column(
        String,
        nullable=False
    )

    stored_name = Column(
        String,
        nullable=False
    )

    file_path = Column(
        String,
        nullable=False
    )

    file_size = Column(
        Integer,
        nullable=False
    )

    uploaded_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )