"""create conditional rules table

Revision ID: eb209b44d040
Revises: 62538de0c854
Create Date: 2026-09-05 10:41:19.153369

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "eb209b44d040"
down_revision: Union[str, Sequence[str], None] = "62538de0c854"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add form_id temporarily as nullable
    op.add_column(
        "conditional_rules",
        sa.Column("form_id", sa.UUID(), nullable=True)
    )

    # 2. Get form_id from the trigger field
    #    fields -> form_versions -> forms
    op.execute("""
        UPDATE conditional_rules cr
        SET form_id = fv.form_id
        FROM fields f
        JOIN form_versions fv
            ON f.form_version_id = fv.id
        WHERE cr.trigger_field_id = f.id
    """)

    # 3. Make comparison_value nullable
    #    This allows the is_empty operator.
    op.alter_column(
        "conditional_rules",
        "comparison_value",
        existing_type=sa.VARCHAR(length=255),
        nullable=True
    )

    # 4. Make sure form_id is filled before making it NOT NULL
    op.alter_column(
        "conditional_rules",
        "form_id",
        existing_type=sa.UUID(),
        nullable=False
    )

    # 5. Add foreign key
    op.create_foreign_key(
        "fk_conditional_rules_form_id",
        "conditional_rules",
        "forms",
        ["form_id"],
        ["id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_conditional_rules_form_id",
        "conditional_rules",
        type_="foreignkey"
    )

    op.alter_column(
        "conditional_rules",
        "comparison_value",
        existing_type=sa.VARCHAR(length=255),
        nullable=False
    )

    op.drop_column(
        "conditional_rules",
        "form_id"
    )