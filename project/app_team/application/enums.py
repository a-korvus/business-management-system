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
