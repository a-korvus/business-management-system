"""app_org models is_active field.

Revision ID: 64dec19a5b8d
Revises: 01df215017c9
Create Date: 2025-05-07 08:31:18.562262
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "64dec19a5b8d"
down_revision: Union[str, None] = "01df215017c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "commands", sa.Column("is_active", sa.Boolean(), nullable=False)
    )
    op.add_column(
        "departments", sa.Column("is_active", sa.Boolean(), nullable=False)
    )
    op.add_column(
        "roles", sa.Column("is_active", sa.Boolean(), nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("roles", "is_active")
    op.drop_column("departments", "is_active")
    op.drop_column("commands", "is_active")
