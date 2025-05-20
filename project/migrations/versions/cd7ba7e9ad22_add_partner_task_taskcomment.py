"""add Partner, Task, TaskComment.

Revision ID: cd7ba7e9ad22
Revises: 35596e55ce51
Create Date: 2025-05-10 13:59:41.278994
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "cd7ba7e9ad22"
down_revision: Union[str, None] = "35596e55ce51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    sa.Enum(
        "FAILED",
        "DONE_DEADLINE_OUT",
        "DONE_DEADLINE",
        "DONE_INITIATIVE",
        name="taskgrade",
    ).create(op.get_bind())
    sa.Enum("OPEN", "IN_PROGRESS", "DONE", name="taskstatus").create(
        op.get_bind()
    )
    op.create_table(
        "partners",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_partners_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_partners_id"), "partners", ["id"], unique=False)
    op.create_index(
        op.f("ix_partners_user_id"), "partners", ["user_id"], unique=True
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "OPEN",
                "IN_PROGRESS",
                "DONE",
                name="taskstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "grade",
            postgresql.ENUM(
                "FAILED",
                "DONE_DEADLINE_OUT",
                "DONE_DEADLINE",
                "DONE_INITIATIVE",
                name="taskgrade",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("assignee_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["partners.id"],
            name="fk_tasks_assignee_partner_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["partners.id"],
            name="fk_tasks_creator_partner_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title"),
    )
    op.create_index(
        op.f("ix_tasks_due_date"), "tasks", ["due_date"], unique=False
    )
    op.create_index(op.f("ix_tasks_id"), "tasks", ["id"], unique=False)
    op.create_table(
        "task_comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("text", sa.String(length=5000), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("commentator_id", sa.UUID(), nullable=True),
        sa.Column("parent_comment_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["commentator_id"],
            ["partners.id"],
            name="fk_taskcomments_commentator_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["parent_comment_id"],
            ["task_comments.id"],
            name="fk_taskcomments_parentcomment_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_taskcomments_task_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_task_comments_id"), "task_comments", ["id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_task_comments_id"), table_name="task_comments")
    op.drop_table("task_comments")
    op.drop_index(op.f("ix_tasks_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_due_date"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_index(op.f("ix_partners_user_id"), table_name="partners")
    op.drop_index(op.f("ix_partners_id"), table_name="partners")
    op.drop_table("partners")
    sa.Enum("OPEN", "IN_PROGRESS", "DONE", name="taskstatus").drop(
        op.get_bind()
    )
    sa.Enum(
        "FAILED",
        "DONE_DEADLINE_OUT",
        "DONE_DEADLINE",
        "DONE_INITIATIVE",
        name="taskgrade",
    ).drop(op.get_bind())
