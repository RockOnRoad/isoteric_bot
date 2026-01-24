"""status mf

Revision ID: 81713241669c
Revises: 95663d03d16a
Create Date: 2026-01-24 13:18:18.809076

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "81713241669c"
down_revision: Union[str, Sequence[str], None] = "95663d03d16a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Fix enum
    op.execute(
        "ALTER TYPE gen_status_enum "
        "ADD VALUE IF NOT EXISTS 'already_generated_today';"
    )

    # 2. Convert request TEXT -> JSONB correctly
    op.execute(
        """
        ALTER TABLE generation_history
        ALTER COLUMN request
        TYPE JSONB
        USING request::jsonb
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE generation_history
        ALTER COLUMN request
        TYPE TEXT
        USING request::text
        """
    )
