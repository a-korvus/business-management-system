"""Drop Partner.

Revision ID: 64cde6d8cb01
Revises: 899d74c48ea7
Create Date: 2025-05-10 19:35:48.044047
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "64cde6d8cb01"
down_revision: Union[str, None] = "899d74c48ea7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        "fk_taskcomments_commentator_id", "task_comments", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_tasks_creator_partner_id", "tasks", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_tasks_assignee_partner_id", "tasks", type_="foreignkey"
    )
    op.drop_index("ix_partners_id", table_name="partners")
    op.drop_index("ix_partners_user_id", table_name="partners")
    op.drop_table("partners")
    op.create_foreign_key(
        "fk_taskcomments_commentator_id",
        "task_comments",
        "users",
        ["commentator_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_tasks_creator_user_id",
        "tasks",
        "users",
        ["creator_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_tasks_assignee_user_id",
        "tasks",
        "users",
        ["assignee_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_tasks_assignee_user_id", "tasks", type_="foreignkey"
    )
    op.drop_constraint("fk_tasks_creator_user_id", "tasks", type_="foreignkey")
    op.create_foreign_key(
        "fk_tasks_creator_partner_id",
        "tasks",
        "partners",
        ["creator_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_tasks_assignee_partner_id",
        "tasks",
        "partners",
        ["assignee_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "fk_taskcomments_commentator_id", "task_comments", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_taskcomments_commentator_id",
        "task_comments",
        "partners",
        ["commentator_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_table(
        "partners",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_partners_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="partners_pkey"),
    )
    op.create_index(
        "ix_partners_user_id", "partners", ["user_id"], unique=True
    )
    op.create_index("ix_partners_id", "partners", ["id"], unique=False)
