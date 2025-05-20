"""Enumerates classes in the 'app_org'."""

import enum


class RoleType(enum.Enum):
    """All possible role values."""

    WORKER = "worker"
    MANAGER = "manager"
    ADMINISTRATOR = "administrator"
    HEAD_OF_DEPARTMENT = "head of department"

    @classmethod
    def get_values(cls) -> list[str]:
        """Get all role names."""
        return [role.value for role in cls]
