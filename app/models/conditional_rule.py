import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ConditionalRule(Base):
    __tablename__ = "conditional_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    form_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forms.id"),
        nullable=False
    )

    trigger_field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=False
    )

    operator: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    comparison_value: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    target_field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=False
    )

    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )