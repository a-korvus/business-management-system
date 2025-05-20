"""role to command.

Revision ID: 35596e55ce51
Revises: 64dec19a5b8d
Create Date: 2025-05-07 09:38:09.471553
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "35596e55ce51"
down_revision: Union[str, None] = "64dec19a5b8d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("roles", sa.Column("command_id", sa.UUID(), nullable=True))
    op.create_index(
        op.f("ix_roles_command_id"), "roles", ["command_id"], unique=False
    )
    op.create_foreign_key(
        "fk_roles_command_id",
        "roles",
        "commands",
        ["command_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_roles_command_id", "roles", type_="foreignkey")
    op.drop_index(op.f("ix_roles_command_id"), table_name="roles")
    op.drop_column("roles", "command_id")
