"""Infrastructure interfaces in the 'app_org'."""

import abc
import uuid

from project.app_org.domain.models import Command, Department, News, Role


class AbstractCommandRepository(abc.ABC):
    """Abstract interface for Command model operations."""

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
    async def get_by_id_detail(self, command_id: uuid.UUID) -> Command | None:
        """Get Command by its ID with all relation models."""
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
    async def add(self, command: Command) -> uuid.UUID:
        """Add Command object to session."""
        raise NotImplementedError


class AbstractDepartmentRepository(abc.ABC):
    """Abstract interface for Department model operations."""

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
    async def get_by_id_detail(
        self,
        department_id: uuid.UUID,
    ) -> Department | None:
        """Get Department by its ID with all relation models."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self) -> list[Department]:
        """Get list of Department objects."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, department: Department) -> uuid.UUID:
        """Add Department object to session."""
        raise NotImplementedError


class AbstractRoleRepository(abc.ABC):
    """Abstract interface for Role model operations."""

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
    async def get_by_id_detail(self, role_id: uuid.UUID) -> Role | None:
        """Get Role by its ID with all relation models."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self) -> list[Role]:
        """Get list of Role objects."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, role: Role) -> uuid.UUID:
        """Add Role object to session."""
        raise NotImplementedError


class AbstractNewsRepository(abc.ABC):
    """Abstract interface for News model operations."""

    @abc.abstractmethod
    async def get_by_id(self, news_id: uuid.UUID) -> News | None:
        """Get News by its ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[News]:
        """Get list of News objects with pagination."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, news: News) -> uuid.UUID:
        """Add News object to session."""
        raise NotImplementedError
