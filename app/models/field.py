import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Field(Base):
    __tablename__ = "fields"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    form_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("form_versions.id"),
        nullable=False
    )

    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    field_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    placeholder: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    validation_config: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )