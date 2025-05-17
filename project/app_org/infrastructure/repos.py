"""Repository interfaces in the 'app_org' app."""

import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import raiseload, selectinload

from project.app_org.application.interfaces import (
    AbstractCommandRepository,
    AbstractDepartmentRepository,
    AbstractNewsRepository,
    AbstractRoleRepository,
)
from project.app_org.domain.models import Command, Department, News, Role
from project.core.db.utils import load_all_relationships


class SACommandRepo(AbstractCommandRepository):
    """Implementation of command repository using sqlalchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize a Command Repository."""
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

    async def get_by_id_detail(self, command_id: uuid.UUID) -> Command | None:
        """Get Command by its ID with all relation models."""
        stmt = (
            select(Command)
            .options(*load_all_relationships(Command))
            .where(Command.id == command_id)
        )

        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_name(self, name: str) -> Command | None:
        """Get the command by name."""
        result = await self._session.execute(
            select(Command).where(Command.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Command]:
        """Get all commands."""
        result = await self._session.execute(
            select(Command)
            .options(raiseload(Command.departments))
            .order_by(Command.created_at)
        )
        return list(result.scalars().all())

    async def add(self, command: Command) -> uuid.UUID:
        """Add new command in sqlalchemy async session."""
        self._session.add(command)
        await self._session.flush([command])
        return command.id


class SADepartmentRepo(AbstractDepartmentRepository):
    """Implementation of department repository using sqlalchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize a Department Repository."""
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

    async def get_by_id_detail(
        self,
        department_id: uuid.UUID,
    ) -> Department | None:
        """Get Department by its ID with all relation models."""
        stmt = (
            select(Department)
            .options(*load_all_relationships(Department))
            .where(Department.id == department_id)
        )

        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_all(self) -> list[Department]:
        """Get all departments."""
        result = await self._session.execute(
            select(Department)
            .options(
                raiseload(Department.command), raiseload(Department.roles)
            )
            .order_by(Department.created_at)
        )
        return list(result.scalars().all())

    async def add(self, department: Department) -> uuid.UUID:
        """Add new department in sqlalchemy async session."""
        self._session.add(department)
        await self._session.flush([department])
        return department.id


class SARoleRepo(AbstractRoleRepository):
    """Implementation of role repository using sqlalchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize a Role Repository."""
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

    async def get_by_id_detail(self, role_id: uuid.UUID) -> Role | None:
        """Get Role by its ID with all relation models."""
        stmt = (
            select(Role)
            .options(*load_all_relationships(Role))
            .where(Role.id == role_id)
        )

        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_all(self) -> list[Role]:
        """Get all roles."""
        result = await self._session.execute(
            select(Role)
            .options(raiseload(Role.department), raiseload(Role.users))
            .order_by(Role.created_at)
        )
        return list(result.scalars().all())

    async def add(self, role: Role) -> uuid.UUID:
        """Add new role in sqlalchemy async session."""
        self._session.add(role)
        await self._session.flush([role])
        return role.id


class SANewsRepo(AbstractNewsRepository):
    """Implementation of news repository using sqlalchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize a News Repository."""
        self._session = session

    async def get_by_id(self, news_id: uuid.UUID) -> News | None:
        """Get the news by ID."""
        result = await self._session.execute(
            select(News).where(News.id == news_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, offset: int = 0, limit: int = 10) -> list[News]:
        """Get all news with pagination."""
        stmt = select(News).order_by(desc(News.created_at))

        if offset > 0:
            stmt = stmt.offset(offset)

        stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, news: News) -> uuid.UUID:
        """Add new news in sqlalchemy async session."""
        self._session.add(news)
        await self._session.flush([news])
        return news.id
