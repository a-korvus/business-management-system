"""Task no unique title.

Revision ID: 899d74c48ea7
Revises: cd7ba7e9ad22
Create Date: 2025-05-10 14:41:29.148441
"""

from typing import Sequence, Union

from alembic import op

revision: str = "899d74c48ea7"
down_revision: Union[str, None] = "cd7ba7e9ad22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("tasks_title_key", "tasks", type_="unique")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_unique_constraint("tasks_title_key", "tasks", ["title"])
