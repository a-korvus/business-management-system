"""Domain SQLAlchemy models in the 'app_team' app."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Self

from sqlalchemy import UUID as UUID_SQL
from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from project.app_team.application.enums import (
    EventType,
    MeetingStatus,
    TaskGrade,
    TaskStatus,
)
from project.core.db.base import Base

if TYPE_CHECKING:
    from project.app_auth.domain.models import User
    from project.app_org.domain.models import Command


meeting_members_table = Table(
    "meeting_users",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "meeting_id",
        ForeignKey("meetings.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

users_calendar_events_table = Table(
    "users_calendar_events",
    Base.metadata,
    Column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "calendar_event_id",
        ForeignKey("calendar_events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Task(Base):
    """Task entity."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_SQL(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(
        String(),
        nullable=True,
        default=None,
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        default=TaskStatus.OPEN,
        nullable=False,
    )
    grade: Mapped[TaskGrade] = mapped_column(
        SQLEnum(TaskGrade),
        nullable=True,
        default=None,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
            name="fk_tasks_creator_user_id",
        ),
        nullable=False,
    )
    assignee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
            name="fk_tasks_assignee_user_id",
        ),
        nullable=False,
    )
    calendar_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "calendar_events.id",
            ondelete="SET NULL",
            name="fk_tasks_calendar_event_id",
        ),
        default=None,
        nullable=True,
    )

    creator: Mapped[User] = relationship(
        "User",
        back_populates="tasks_created",
        foreign_keys=[creator_id],
    )
    assignee: Mapped[User] = relationship(
        "User",
        back_populates="tasks_assigned",
        foreign_keys=[assignee_id],
    )
    comments: Mapped[list[TaskComment]] = relationship(
        "TaskComment",
        back_populates="task",
    )
    calendar_event: Mapped[CalendarEvent | None] = relationship(
        "CalendarEvent",
        back_populates="related_task",
    )


class TaskComment(Base):
    """Comment to the task."""

    __tablename__ = "task_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_SQL(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    text: Mapped[str] = mapped_column(
        String(length=5000),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "tasks.id",
            ondelete="CASCADE",
            name="fk_taskcomments_task_id",
        ),
        nullable=False,
    )
    commentator_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
            name="fk_taskcomments_commentator_id",
        ),
        nullable=True,
    )
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "task_comments.id",
            ondelete="RESTRICT",
            name="fk_taskcomments_parentcomment_id",
        ),
        nullable=True,
        default=None,
    )

    task: Mapped[Task] = relationship(
        "Task",
        back_populates="comments",
    )
    commentator: Mapped[User] = relationship(
        "User",
        back_populates="task_comments",
    )

    # 'многие-к-одному' с точки зрения дочернего комментария
    parent_comment: Mapped[Self | None] = relationship(
        "TaskComment",
        foreign_keys=[parent_comment_id],  # указываем PK для этой связи
        remote_side=[id],  # столбец 'id' в таблице 'task_comments' является
        # "удаленной" (родительской) стороной этой конкретной связи
        back_populates="child_comments",
    )
    # 'один-ко-многим' с точки зрения родительского комментария
    child_comments: Mapped[list[Self]] = relationship(
        "TaskComment",
        back_populates="parent_comment",
    )


class Meeting(Base):
    """Team meeting entity."""

    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_SQL(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(
        String(),
        nullable=True,
        default=None,
    )
    status: Mapped[MeetingStatus] = mapped_column(
        SQLEnum(MeetingStatus),
        default=MeetingStatus.PLANNED,
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    creator_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
            name="fk_meetings_creator_user_id",
        ),
        nullable=True,
    )
    command_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "commands.id",
            ondelete="RESTRICT",
            name="fk_meetings_command_id",
        ),
        nullable=False,
    )
    calendar_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "calendar_events.id",
            ondelete="RESTRICT",
            name="fk_meetings_calendar_event_id",
        ),
        nullable=False,
    )

    creator: Mapped[User] = relationship(
        "User",
        back_populates="meetengs_created",
    )
    command: Mapped[Command] = relationship(
        "Command",
        back_populates="meetings",
    )
    members: Mapped[list[User]] = relationship(
        "User",
        secondary=meeting_members_table,
        back_populates="meetings_memberships",
        lazy="selectin",
    )
    calendar_event: Mapped[CalendarEvent] = relationship(
        "CalendarEvent",
        back_populates="related_meeting",
        lazy="joined",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the meeting. Create a calendar event together with."""
        meet_members: list[User] | None = None
        if "meet_members" in kwargs:
            meet_members = kwargs.pop("meet_members")

        super().__init__(*args, **kwargs)

        if not hasattr(self, "calendar_event") or self.calendar_event is None:
            self.calendar_event = CalendarEvent(
                title=self.topic,
                start_time=self.start_time,
                end_time=self.end_time,
                event_type=EventType.MEETING,
            )

        if meet_members:
            self.add_members(meet_members)

    def add_members(self, new_members: list[User]) -> None:
        """Add new memebers to the meeting and related event."""
        self.members.extend(new_members)
        self.calendar_event.users.extend(new_members)


class CalendarEvent(Base):
    """Team event entity."""

    __tablename__ = "calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_SQL(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(
        String(),
        nullable=True,
        default=None,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType),
        default=EventType.GENERAL,
        nullable=False,
    )
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    users: Mapped[list[User]] = relationship(
        "User",
        secondary=users_calendar_events_table,
        back_populates="calendar_events",
    )
    related_task: Mapped[Task | None] = relationship(
        "Task",
        back_populates="calendar_event",
    )
    related_meeting: Mapped[Meeting | None] = relationship(
        "Meeting",
        back_populates="calendar_event",
    )
