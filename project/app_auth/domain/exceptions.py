"""Custom exeptions to use in the domain models."""

import uuid

from project.core.exceptions import DomainError


class UserNotFound(DomainError):
    """Exception if the User does not exist."""

    def __init__(
        self,
        user_id: uuid.UUID | str | None = None,
        email: str | None = None,
    ):
        """Initialize the exception."""
        self.user_id = user_id
        self.email = email

        if user_id:
            super().__init__(f"User with id '{user_id}' not found.")
        elif email:
            super().__init__(f"User with email '{email}' not found.")
        else:
            super().__init__("User not found.")


class EmailAlreadyExists(DomainError):
    """Exception if the email is already in use."""

    def __init__(self, email: str):
        """Initialize the exception."""
        self.email = email

        super().__init__(f"Email '{email}' is already registered.")


class AuthenticationError(DomainError):
    """Exception if the authentication error occurs."""

    def __init__(self, msg: str = "Invalid credentials") -> None:
        """Initialize the exception."""
        super().__init__(msg)


class InvalidPasswordFormatError(DomainError):
    """Incorrect format of saved password hash."""

    def __init__(self, msg: str = "Invalid stored password format") -> None:
        """Initialize the exception."""
        super().__init__(msg)
