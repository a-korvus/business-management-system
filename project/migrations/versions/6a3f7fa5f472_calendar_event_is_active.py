"""calendar event is active.

Revision ID: 6a3f7fa5f472
Revises: 9335fa062567
Create Date: 2025-05-12 17:12:45.862174
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "6a3f7fa5f472"
down_revision: Union[str, None] = "9335fa062567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "calendar_events", sa.Column("is_active", sa.Boolean(), nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("calendar_events", "is_active")
