"""calendar event create & update dates.

Revision ID: 9335fa062567
Revises: 64e4bea1ec3d
Create Date: 2025-05-12 13:59:28.682243
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9335fa062567"
down_revision: Union[str, None] = "64e4bea1ec3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "calendar_events",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "calendar_events",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("calendar_events", "updated_at")
    op.drop_column("calendar_events", "created_at")
