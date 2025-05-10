"""Validation schemas for domain models in the 'app_team'."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from project.app_team.application.enums import TaskGrade, TaskStatus


class TaskBase(BaseModel):
    """Task base schema."""

    description: str | None = None


class TaskCreate(TaskBase):
    """Validate the task input data."""

    title: str = Field(..., max_length=500)
    due_date: datetime
    creator_id: uuid.UUID
    assignee_id: uuid.UUID


class TaskUpdate(TaskBase):
    """Update existing task."""

    title: str | None = Field(default=None, max_length=500)
    status: TaskStatus | None = None
    grade: TaskGrade | None = None
    due_date: datetime | None = None
    assignee_id: uuid.UUID | None = None


class TaskRead(TaskBase):
    """Schema to serialize the existing task data."""

    id: uuid.UUID
    title: str
    status: TaskStatus
    grade: TaskGrade | None
    is_active: bool
    due_date: datetime
    created_at: datetime
    updated_at: datetime
    creator_id: uuid.UUID
    assignee_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class TaskCommentBase(BaseModel):
    """Task comment base schema."""

    text: str = Field(..., max_length=5000)


class TaskCommentCreate(TaskCommentBase):
    """Validate the task comment input data."""

    task_id: uuid.UUID
    commentator_id: uuid.UUID
    parent_comment_id: uuid.UUID | None = None


class TaskCommentUpdate(TaskCommentBase):
    """Update existing task comment."""

    ...


class TaskCommentRead(TaskCommentBase):
    """Schema to serialize the existing task comment data."""

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    task_id: uuid.UUID
    commentator_id: uuid.UUID
    parent_comment_id: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)
