"""Custom exceptions to use in the domain models."""

import uuid

from project.core.exceptions import DomainError


class CommandNotFound(DomainError):
    """Exception if a Command does not exist."""

    def __init__(
        self,
        command_id: uuid.UUID | str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize the exception."""
        self.command_id = command_id
        self.name = name

        if command_id:
            super().__init__(f"Command with id '{command_id}' not found.")
        elif name:
            super().__init__(f"Command with name '{name}' not found.")
        else:
            super().__init__("Command not found.")


class CommandNameExistsError(DomainError):
    """Attempt to create/update a Command with an existing name."""

    def __init__(self, name: str) -> None:
        """Initialize the exception."""
        self.name = name
        super().__init__(f"Command with name '{name}' already exists.")


class CommandNotEmpty(DomainError):
    """Attempt to deactivate a Command with existing relationships."""

    def __init__(self, command_name: str, rel_names: list[str]) -> None:
        """Initialize the exception."""
        self.command_name = command_name
        self.active_relationships = ", ".join(rel_names) if rel_names else None
        super().__init__(
            f"Command '{self.command_name}' has active relationships: "
            f"'{self.active_relationships}'."
        )


class DepartmentNotFound(DomainError):
    """Exception if a Department does not exist."""

    def __init__(self, department_id: uuid.UUID) -> None:
        """Initialize the exception."""
        self.department_id = department_id

        super().__init__(f"Department with id '{department_id}' not found.")


class DepartmentNotInCommand(DomainError):
    """Exception if the Command not contains the Department."""

    def __init__(self, department_id: uuid.UUID) -> None:
        """Initialize the exception."""
        self.department_id = department_id

        super().__init__(f"Department with id '{department_id}' not found.")


class DepartmentNotEmpty(DomainError):
    """Attempt to deactivate a Department with existing relationships."""

    def __init__(self, department_name: str, rel_names: list[str]) -> None:
        """Initialize the exception."""
        self.department_name = department_name
        self.active_relationships = ", ".join(rel_names) if rel_names else None
        super().__init__(
            f"Department '{self.department_name}' has active relationships: "
            f"'{self.active_relationships}'."
        )


class RoleNotFound(DomainError):
    """Exception if a Role does not exist."""

    def __init__(self, role_id: uuid.UUID) -> None:
        """Initialize the exception."""
        self.role_id = role_id

        super().__init__(f"Role with id '{role_id}' not found.")


class RoleNotEmpty(DomainError):
    """Attempt to deactivate a Role with existing relationships."""

    def __init__(self, role_name: str, rel_names: list[str]) -> None:
        """Initialize the exception."""
        self.role_name = role_name
        self.active_relationships = ", ".join(rel_names) if rel_names else None
        super().__init__(
            f"Role '{self.role_name}' has active relationships: "
            f"'{self.active_relationships}'."
        )


class NewsNotFound(DomainError):
    """Exception if a News does not exist."""

    def __init__(self, news_id: uuid.UUID) -> None:
        """Initialize the exception."""
        self.news_id = news_id

        super().__init__(f"Role with id '{news_id}' not found.")
