"""meeting, calendar.

Revision ID: 64e4bea1ec3d
Revises: 64cde6d8cb01
Create Date: 2025-05-12 13:09:31.425425
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "64e4bea1ec3d"
down_revision: Union[str, None] = "64cde6d8cb01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    sa.Enum("TASK", "MEETING", "GENERAL", name="eventtype").create(
        op.get_bind()
    )
    sa.Enum("PLANNED", "COMPLETED", "CANCELLED", name="meetingstatus").create(
        op.get_bind()
    )
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "event_type",
            postgresql.ENUM(
                "TASK",
                "MEETING",
                "GENERAL",
                name="eventtype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("all_day", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_calendar_events_end_time"),
        "calendar_events",
        ["end_time"],
        unique=False,
    )
    op.create_index(
        op.f("ix_calendar_events_id"), "calendar_events", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_calendar_events_start_time"),
        "calendar_events",
        ["start_time"],
        unique=False,
    )
    op.create_table(
        "meetings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("topic", sa.String(length=500), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PLANNED",
                "COMPLETED",
                "CANCELLED",
                name="meetingstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
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
        sa.Column("creator_id", sa.UUID(), nullable=True),
        sa.Column("command_id", sa.UUID(), nullable=False),
        sa.Column("calendar_event_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["calendar_event_id"],
            ["calendar_events.id"],
            name="fk_meetings_calendar_event_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["command_id"],
            ["commands.id"],
            name="fk_meetings_command_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["users.id"],
            name="fk_meetings_creator_user_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_meetings_end_time"), "meetings", ["end_time"], unique=False
    )
    op.create_index(op.f("ix_meetings_id"), "meetings", ["id"], unique=False)
    op.create_index(
        op.f("ix_meetings_start_time"),
        "meetings",
        ["start_time"],
        unique=False,
    )
    op.create_table(
        "users_calendar_events",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("calendar_event_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["calendar_event_id"], ["calendar_events.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "calendar_event_id"),
    )
    op.create_table(
        "meeting_users",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("meeting_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["meeting_id"], ["meetings.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "meeting_id"),
    )
    op.add_column(
        "tasks", sa.Column("calendar_event_id", sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        "fk_tasks_calendar_event_id",
        "tasks",
        "calendar_events",
        ["calendar_event_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_tasks_calendar_event_id", "tasks", type_="foreignkey"
    )
    op.drop_column("tasks", "calendar_event_id")
    op.drop_table("meeting_users")
    op.drop_table("users_calendar_events")
    op.drop_index(op.f("ix_meetings_start_time"), table_name="meetings")
    op.drop_index(op.f("ix_meetings_id"), table_name="meetings")
    op.drop_index(op.f("ix_meetings_end_time"), table_name="meetings")
    op.drop_table("meetings")
    op.drop_index(
        op.f("ix_calendar_events_start_time"), table_name="calendar_events"
    )
    op.drop_index(op.f("ix_calendar_events_id"), table_name="calendar_events")
    op.drop_index(
        op.f("ix_calendar_events_end_time"), table_name="calendar_events"
    )
    op.drop_table("calendar_events")
    sa.Enum("PLANNED", "COMPLETED", "CANCELLED", name="meetingstatus").drop(
        op.get_bind()
    )
    sa.Enum("TASK", "MEETING", "GENERAL", name="eventtype").drop(op.get_bind())
