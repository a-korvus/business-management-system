"""Custom exceptions to use in the domain models."""

import uuid

from project.core.exceptions import DomainError


class TaskNotFound(DomainError):
    """Exception if a Task does not exist."""

    def __init__(self, task_id: uuid.UUID) -> None:
        """Initialize the exception."""
        self.task_id = task_id

        super().__init__(f"Task with id '{task_id}' not found.")


class TaskCommentNotFound(DomainError):
    """Exception if a Task Comment does not exist."""

    def __init__(self, task_comment_id: uuid.UUID) -> None:
        """Initialize the exception."""
        self.task_comment_id = task_comment_id

        super().__init__(f"TaskComment with id '{task_comment_id}' not found.")


class CalendarEventNotFound(DomainError):
    """Exception if a Calendar Event does not exist."""

    def __init__(self, c_event_id: uuid.UUID) -> None:
        """Initialize the exception."""
        self.c_event_id = c_event_id

        super().__init__(f"CalendarEvent with id '{c_event_id}' not found.")


class OverlapError(ValueError):
    """Exception if user already has an event for the specified period."""

    def __init__(self, c_event_id: uuid.UUID) -> None:
        """Initialize the exception."""
        self.c_event_id = c_event_id

        super().__init__(f"Unable to add user to event '{c_event_id}'.")


class MeetingNotFound(DomainError):
    """Exception if a Meeting does not exist."""

    def __init__(self, meeting_id: uuid.UUID) -> None:
        """Initialize the exception."""
        self.meeting_id = meeting_id

        super().__init__(f"Meeting with id '{meeting_id}' not found.")
