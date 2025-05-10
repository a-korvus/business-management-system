"""Custom exeptions to use in the domain models."""

import uuid

from project.core.exceptions import DomainError


class PartnerNotFound(DomainError):
    """Exception if a Partner does not exist."""

    def __init__(
        self,
        partner_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        user_email: str | None = None,
    ) -> None:
        """Initialize the exception."""
        self.partner_id = partner_id
        self.user_id = user_id
        self.user_email = user_email

        if partner_id:
            super().__init__(f"Partner with id '{partner_id}' not found.")
        elif user_id:
            super().__init__(
                f"Partner for user with id '{user_id}' not found."
            )
        elif user_email:
            super().__init__(
                f"Partner for user with email '{user_email}' not found."
            )
        else:
            super().__init__("Partner not found.")


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
