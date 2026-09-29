"""add form starts table

Revision ID: 98a514bf649a
Revises: bdc4c15714bf
Create Date: 2026-09-17 07:07:05.731781

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "98a514bf649a"

down_revision: Union[str, Sequence[str], None] = "bdc4c15714bf"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "form_starts",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "form_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ["form_version_id"],
            ["form_versions.id"]
        ),

        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("form_starts")