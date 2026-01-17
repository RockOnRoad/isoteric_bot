"""allowed user.status = None

Revision ID: 3bce99b99cd2
Revises: 8cda14a63c92
Create Date: 2026-01-16 21:12:37.409071

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3bce99b99cd2"
down_revision: Union[str, Sequence[str], None] = "8cda14a63c92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "users",
        "segment",
        existing_type=postgresql.ENUM(
            "lead", "qual", "client", "banned", name="segment_enum"
        ),
        nullable=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "users",
        "segment",
        existing_type=postgresql.ENUM(
            "lead", "qual", "client", "banned", name="segment_enum"
        ),
        nullable=False,
    )
    # ### end Alembic commands ###
