"""user-command relation.

Revision ID: 01df215017c9
Revises: 6394d9b2783a
Create Date: 2025-05-05 18:20:49.938354

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "01df215017c9"
down_revision: Union[str, None] = "6394d9b2783a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("command_id", sa.UUID(), nullable=True))
    op.create_index(
        op.f("ix_users_command_id"), "users", ["command_id"], unique=False
    )
    op.create_foreign_key(
        "fk_users_command_id",
        "users",
        "commands",
        ["command_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_users_command_id", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_command_id"), table_name="users")
    op.drop_column("users", "command_id")
