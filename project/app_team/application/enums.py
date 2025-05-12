"""Enumerates classes in the 'app_team'."""

import enum


@enum.unique
class TaskStatus(enum.StrEnum):
    """Task status values."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@enum.unique
class TaskGrade(enum.IntEnum):
    """Task grade values."""

    FAILED = 0
    DONE_DEADLINE_OUT = 1
    DONE_DEADLINE = 2
    DONE_INITIATIVE = 3

    @classmethod
    def get_values(cls) -> list[int]:
        """Get all grades."""
        return [grade.value for grade in cls]


@enum.unique
class MeetingStatus(enum.StrEnum):
    """Meeting status values."""

    PLANNED = "planned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@enum.unique
class EventType(enum.StrEnum):
    """Event type values."""

    TASK = "task"
    MEETING = "meeting"
    GENERAL = "general"
