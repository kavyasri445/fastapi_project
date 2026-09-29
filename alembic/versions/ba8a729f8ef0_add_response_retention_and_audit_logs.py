"""add response retention and audit logs

Revision ID: ba8a729f8ef0
Revises: 98a514bf649a
Create Date: 2026-09-19 16:28:25.020991

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "ba8a729f8ef0"

down_revision: Union[str, Sequence[str], None] = "98a514bf649a"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # =========================================================
    # SUBMISSIONS - ARCHIVE SUPPORT
    # =========================================================

    op.add_column(
        "submissions",
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false")
        )
    )

    op.add_column(
        "submissions",
        sa.Column(
            "archived_at",
            sa.DateTime(),
            nullable=True
        )
    )

    # Remove the server-side default after existing rows
    # have been initialized to False.
    op.alter_column(
        "submissions",
        "is_archived",
        server_default=None
    )

    # =========================================================
    # AUDIT LOGS TABLE
    # =========================================================

    op.create_table(
        "audit_logs",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True
        ),

        sa.Column(
            "action",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "entity_type",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "entity_id",
            sa.String(),
            nullable=True
        ),

        sa.Column(
            "details",
            sa.Text(),
            nullable=True
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"]
        ),

        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    """Downgrade schema."""

    # =========================================================
    # REMOVE AUDIT LOGS
    # =========================================================

    op.drop_table("audit_logs")

    # =========================================================
    # REMOVE ARCHIVE SUPPORT
    # =========================================================

    op.drop_column(
        "submissions",
        "archived_at"
    )

    op.drop_column(
        "submissions",
        "is_archived"
    )

    # =========================================================
    # IMPORTANT
    # =========================================================
    # Do NOT drop form_starts here.
    # That table already exists and belongs to the
    # previously completed form-start tracking work.