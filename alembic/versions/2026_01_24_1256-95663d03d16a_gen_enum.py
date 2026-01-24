"""gen enum

Revision ID: 95663d03d16a
Revises: 7e5a08b08723
Create Date: 2026-01-24 12:56:48.819155

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "95663d03d16a"
down_revision: Union[str, Sequence[str], None] = "7e5a08b08723"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create enum type explicitly
    gen_status_enum = sa.Enum(
        "success",
        "error",
        "not_enough_balance",
        "already_generated_today",
        name="gen_status_enum",
    )
    gen_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add column using that enum
    op.add_column(
        "generation_history",
        sa.Column("gen_status", gen_status_enum, nullable=False),
    )

    # 3. Other ops
    op.alter_column(
        "generation_history",
        "request",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.TEXT(),
        existing_nullable=False,
        postgresql_using="request::text",
    )

    op.drop_column("generation_history", "gen_successful")
    op.drop_column("generation_history", "timestamp")


def downgrade() -> None:
    # 1. Restore dropped columns
    op.add_column(
        "generation_history",
        sa.Column(
            "timestamp",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
        ),
    )
    op.add_column(
        "generation_history",
        sa.Column("gen_successful", sa.BOOLEAN(), nullable=False),
    )

    op.alter_column(
        "generation_history",
        "request",
        existing_type=sa.TEXT(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="request::jsonb",
    )

    # 2. Drop enum-backed column
    op.drop_column("generation_history", "gen_status")

    # 3. Drop enum type
    gen_status_enum = sa.Enum(name="gen_status_enum")
    gen_status_enum.drop(op.get_bind(), checkfirst=True)
