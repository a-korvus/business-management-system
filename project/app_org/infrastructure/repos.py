"""Repository interfaces in the 'app_org' app."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import raiseload, selectinload

from project.app_org.application.interfaces import (
    AbsCommandRepository,
    AbsDepartmentRepository,
    AbsNewsRepository,
    AbsRoleRepository,
)
from project.app_org.domain.models import Command, Department, News, Role


class SACommandRepo(AbsCommandRepository):
    """Implementation of command repository using sqlalchemy."""

    def __init__(self, session: AsyncSession | None) -> None:
        """Initialize a Command Repository."""
        if session is None:
            raise ValueError(f"{self.__class__.__name__} get an empty session")

        self._session = session

    async def get_by_id(self, command_id: uuid.UUID) -> Command | None:
        """Get the command by ID."""
        result = await self._session.execute(
            select(Command).where(Command.id == command_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_departments(
        self,
        command_id: uuid.UUID,
    ) -> Command | None:
        """Get the command by ID.

        Use options to load related departments.
        """
        result = await self._session.execute(
            select(Command)
            .options(selectinload(Command.departments))
            .where(Command.id == command_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Command | None:
        """Get the command by name."""
        result = await self._session.execute(
            select(Command).where(Command.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Command]:
        """Get all commands."""
        result = await self._session.execute(
            select(Command).options(raiseload(Command.departments))
        )
        return list(result.scalars().all())

    async def add(self, command: Command) -> None:
        """Add new command in sqlalchemy async session."""
        self._session.add(command)


class SADepartmentRepo(AbsDepartmentRepository):
    """Implementation of department repository using sqlalchemy."""

    def __init__(self, session: AsyncSession | None) -> None:
        """Initialize a Department Repository."""
        if session is None:
            raise ValueError(f"{self.__class__.__name__} get an empty session")

        self._session = session

    async def get_by_id(self, department_id: uuid.UUID) -> Department | None:
        """Get the department by ID."""
        result = await self._session.execute(
            select(Department).where(Department.id == department_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_roles(
        self,
        department_id: uuid.UUID,
    ) -> Department | None:
        """Get the department by ID.

        Use options to load related roles.
        """
        result = await self._session.execute(
            select(Department)
            .options(selectinload(Department.roles))
            .where(Department.id == department_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Department]:
        """Get all departments."""
        result = await self._session.execute(
            select(Department).options(
                raiseload(Department.command), raiseload(Department.roles)
            )
        )
        return list(result.scalars().all())

    async def add(self, department: Department) -> None:
        """Add new department in sqlalchemy async session."""
        self._session.add(department)


class SARoleRepo(AbsRoleRepository):
    """Implementation of role repository using sqlalchemy."""

    def __init__(self, session: AsyncSession | None) -> None:
        """Initialize a Role Repository."""
        if session is None:
            raise ValueError(f"{self.__class__.__name__} get an empty session")

        self._session = session

    async def get_by_id(self, role_id: uuid.UUID) -> Role | None:
        """Get the role by ID."""
        result = await self._session.execute(
            select(Role)
            .options(raiseload(Role.department), raiseload(Role.users))
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_users(
        self,
        role_id: uuid.UUID,
    ) -> Role | None:
        """Get Role by its ID with related users."""
        result = await self._session.execute(
            select(Role)
            .options(selectinload(Role.users))
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Role]:
        """Get all role."""
        result = await self._session.execute(
            select(Role).options(
                raiseload(Role.department), raiseload(Role.users)
            )
        )
        return list(result.scalars().all())

    async def add(self, role: Role) -> None:
        """Add new role in sqlalchemy async session."""
        self._session.add(role)


class SANewsRepo(AbsNewsRepository):
    """Implementation of news repository using sqlalchemy."""

    def __init__(self, session: AsyncSession | None) -> None:
        """Initialize a News Repository."""
        if session is None:
            raise ValueError(f"{self.__class__.__name__} get an empty session")

        self._session = session

    async def get_by_id(self, news_id: uuid.UUID) -> News | None:
        """Get the news by ID."""
        result = await self._session.execute(
            select(News).where(News.id == news_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[News]:
        """Get all news."""
        result = await self._session.execute(select(News))
        return list(result.scalars().all())

    async def add(self, news: News) -> None:
        """Add new news in sqlalchemy async session."""
        self._session.add(news)
