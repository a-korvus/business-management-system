"""Infrastructure interfaces in the 'app_auth' app."""

from __future__ import annotations

import abc
import uuid
from types import TracebackType
from typing import Protocol, Self, runtime_checkable

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
    """Interface for implementing model-specific User operations."""

    @abc.abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> "User" | None:
        """Get User by its ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_email(self, email: str) -> "User" | None:
        """Get User by its email."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self) -> list["User"]:
        """Get list of User objects."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, user: "User") -> None:
        """Add User object to session."""
        raise NotImplementedError


class AbstractUnitOfWork(abc.ABC):
    """Interface for implementing app-specific authentication actions."""

    users: AbstractUserRepository

    async def __aenter__(self) -> Self:
        """Enter to async context manager."""
        raise NotImplementedError

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit from async context manager."""
        raise NotImplementedError

    @abc.abstractmethod
    async def commit(self) -> None:
        """Commit changes within a session."""
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self) -> None:
        """Rollback changes within a session."""
        raise NotImplementedError
