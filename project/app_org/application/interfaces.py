"""Infrastructure interfaces in the 'app_org' app."""

import abc
import uuid
from types import TracebackType
from typing import Self, Sequence, TypeVar

from project.app_org.domain.models import Command, Department, News, Role
from project.core.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class AbsCommandRepository(abc.ABC):
    """Interface for implementing model-specific Command operations."""

    @abc.abstractmethod
    async def get_by_id(self, command_id: uuid.UUID) -> Command | None:
        """Get Command by its ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id_with_departments(
        self,
        command_id: uuid.UUID,
    ) -> Command | None:
        """Get Command by its ID with related departments."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_name(self, name: str) -> Command | None:
        """Get Command by its name."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self) -> list[Command]:
        """Get list of Command objects."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, command: Command) -> None:
        """Add Command object to session."""
        raise NotImplementedError


class AbsDepartmentRepository(abc.ABC):
    """Interface for implementing model-specific Department operations."""

    @abc.abstractmethod
    async def get_by_id(self, department_id: uuid.UUID) -> Department | None:
        """Get Department by its ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id_with_roles(
        self,
        department_id: uuid.UUID,
    ) -> Department | None:
        """Get Department by its ID with related roles."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self) -> list[Department]:
        """Get list of Department objects."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, department: Department) -> None:
        """Add Department object to session."""
        raise NotImplementedError


class AbsRoleRepository(abc.ABC):
    """Interface for implementing model-specific Role operations."""

    @abc.abstractmethod
    async def get_by_id(self, role_id: uuid.UUID) -> Role | None:
        """Get Role by its ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id_with_users(
        self,
        role_id: uuid.UUID,
    ) -> Role | None:
        """Get Role by its ID with related users."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self) -> list[Role]:
        """Get list of Role objects."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, role: Role) -> None:
        """Add Role object to session."""
        raise NotImplementedError


class AbsNewsRepository(abc.ABC):
    """Interface for implementing model-specific News operations."""

    @abc.abstractmethod
    async def get_by_id(self, news_id: uuid.UUID) -> News | None:
        """Get News by its ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self) -> list[News]:
        """Get list of News objects."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, news: News) -> None:
        """Add News object to session."""
        raise NotImplementedError


class AbsUnitOfWork(abc.ABC):
    """Interface for implementing app-specific authentication actions."""

    commands: AbsCommandRepository
    departments: AbsDepartmentRepository
    roles: AbsRoleRepository
    news: AbsNewsRepository

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
    async def refresh(
        self,
        instance: ModelType,
        attribute_names: Sequence[str] | None = None,
    ) -> None:
        """Refresh the given instance from the database."""
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self) -> None:
        """Rollback changes within a session."""
        raise NotImplementedError
