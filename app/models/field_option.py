import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class FieldOption(Base):
    __tablename__ = "field_options"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=False
    )

    option_label: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    option_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )