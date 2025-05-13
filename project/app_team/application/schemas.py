"""Validation schemas for domain models in the 'app_team'."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from project.app_team.application.enums import (
    EventType,
    MeetingStatus,
    TaskGrade,
    TaskStatus,
)


class TaskBase(BaseModel):
    """Task base schema."""

    description: str | None = None


class TaskCreate(TaskBase):
    """Validate the task input data."""

    title: str = Field(..., max_length=500)
    due_date: datetime
    creator_id: uuid.UUID
    assignee_id: uuid.UUID
    calendar_event_id: uuid.UUID | None = None

    @field_validator("due_date", mode="after")
    @classmethod
    def sure_future_date(cls, value: datetime) -> datetime:
        """Make sure that the due date is not in the past."""
        if value.date() < date.today():
            raise ValueError("Due date must be in the future.")

        return value


class TaskUpdate(TaskBase):
    """Update existing task."""

    title: str | None = Field(default=None, max_length=500)
    status: TaskStatus | None = None
    grade: TaskGrade | None = None
    due_date: datetime | None = None
    assignee_id: uuid.UUID | None = None
    calendar_event_id: uuid.UUID | None = None


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
    calendar_event_id: uuid.UUID | None

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


class Period(BaseModel):
    """Scheme of checking the period boundaries."""

    start: date = Field(..., description="Period start date (YYYY-MM-DD)")
    end: date = Field(..., description="Period end date (YYYY-MM-DD)")

    @model_validator(mode="after")
    def check_dates_order(self) -> Self:
        """Make sure the end date more or equal the start date."""
        if self.end < self.start:
            raise ValueError(
                "The end date cannot be less than the start date."
            )
        return self


class MeetingBase(BaseModel):
    """Meeting base schema."""


class MeetingCreate(BaseModel):
    """Validate the meeting input data."""

    topic: str | None = Field(..., max_length=500)
    description: str | None = None
    status: MeetingStatus | None = None
    start_time: datetime
    end_time: datetime
    creator_id: uuid.UUID
    command_id: uuid.UUID
    members_ids: list[uuid.UUID]


class MeetingUpdate(BaseModel):
    """Update existing meeting event."""

    topic: str | None = Field(default=None, max_length=500)
    description: str | None = None
    status: MeetingStatus | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class MeetingRead(BaseModel):
    """Schema to serialize the existing meeting data."""

    id: uuid.UUID
    topic: str
    description: str | None
    status: MeetingStatus
    start_time: datetime
    end_time: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    creator_id: uuid.UUID | None
    command_id: uuid.UUID
    calendar_event_id: uuid.UUID


class CalendarEventBase(BaseModel):
    """Calendar event base schema."""

    description: str | None = None
    all_day: bool | None = False


class CalendarEventCreate(CalendarEventBase):
    """Validate the calendar event input data."""

    title: str = Field(..., max_length=500)
    start_time: datetime
    end_time: datetime
    event_type: EventType | None = EventType.GENERAL

    @model_validator(mode="after")
    def check_dates_order(self) -> Self:
        """Make sure the end date more or equal the start date."""
        if self.end_time < self.start_time:
            raise ValueError(
                "The end date cannot be less than the start date."
            )
        return self


class CalendarEventUpdate(CalendarEventBase):
    """Update existing calendar event."""

    title: str | None = Field(default=None, max_length=500)
    start_time: datetime | None = None
    end_time: datetime | None = None
    event_type: EventType | None = None


class CalendarEventRead(CalendarEventBase):
    """Schema to serialize the existing calendar event data."""

    id: uuid.UUID
    title: str
    start_time: datetime
    end_time: datetime
    event_type: EventType
    created_at: datetime
    updated_at: datetime


class UserToEvent(BaseModel):
    """Schema to validate related variables."""

    user_id: uuid.UUID
    event_id: uuid.UUID
