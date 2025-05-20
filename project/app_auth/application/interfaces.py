"""Infrastructure interfaces in the 'app_auth' app."""

from __future__ import annotations

import abc
import uuid
from typing import Protocol, runtime_checkable

from project.app_auth.domain.models import User


@runtime_checkable
class PasswordHasher(Protocol):
    """Interface for hashing and checking passwords."""

    def hash_password(self, plain_pswrd: str) -> str:
        """Encrypt the password."""
        ...

    def verify_password(self, plain_pswrd: str, stored_pswrd: str) -> bool:
        """Verify plain password is an encrypted password."""
        ...


class AbstractUserRepository(abc.ABC):
    """Abstract interface for User model operations."""

    @abc.abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get User by its ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id_profile(self, user_id: uuid.UUID) -> User | None:
        """Get the user by ID with profile."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id_role(self, user_id: uuid.UUID) -> User | None:
        """Get the user by ID with role."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id_detail(self, user_id: uuid.UUID) -> User | None:
        """Get User by its ID with all relationships."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Get User by its email."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_email_detail(self, email: str) -> User | None:
        """Get User by its email with all relationships."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[User]:
        """Get list of User objects with pagination."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, user: User) -> None:
        """Add User object to session."""
        raise NotImplementedError

    @abc.abstractmethod
    async def check_command_exists(self, command_id: uuid.UUID) -> bool:
        """Check that the command exists."""
