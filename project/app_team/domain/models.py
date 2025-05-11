"""Domain SQLAlchemy models in the 'app_team' app."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Self

from sqlalchemy import UUID as UUID_SQL
from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from project.app_team.application.enums import TaskGrade, TaskStatus
from project.core.db.base import Base

if TYPE_CHECKING:
    from project.app_auth.domain.models import User


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
