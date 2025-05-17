"""Repository interfaces in the 'app_auth' app."""

import uuid

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from project.app_auth.application.interfaces import AbstractUserRepository
from project.app_auth.domain.models import User
from project.app_org.domain.models import Command


class SAUserRepository(AbstractUserRepository):
    """Implementation of user repository using sqlalchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize a User Repository."""
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get the user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_profile(self, user_id: uuid.UUID) -> User | None:
        """Get the user by ID with profile."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_role(self, user_id: uuid.UUID) -> User | None:
        """Get the user by ID with role."""
        stmt = (
            select(User)
            .options(selectinload(User.role))
            .where(User.id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_detail(self, user_id: uuid.UUID) -> User | None:
        """Get the user by ID. Load related objects."""
        stmt = (
            select(User)
            .options(
                selectinload(User.profile),
                selectinload(User.command),
                selectinload(User.role),
            )
            .where(User.id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get the user by email. Load related profile."""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_detail(self, email: str) -> User | None:
        """Get the user by email. Load related objects."""
        stmt = (
            select(User)
            .options(
                selectinload(User.profile),
                selectinload(User.command),
                selectinload(User.role),
            )
            .where(User.email == email)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, offset: int = 0, limit: int = 10) -> list[User]:
        """Get users with pagination.

        Args:
            offset (int, optional): Number of records to skip for pagination.
                Defaults to 0.
            limit (int, optional): Maximum number of records to return.
                Defaults to 10.

        Returns:
            list[User]: A list of users.
        """
        stmt = select(User).order_by(User.created_at)

        if offset > 0:
            stmt = stmt.offset(offset)

        stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, user: User) -> None:
        """Add a new user to a session within the current transaction."""
        self._session.add(user)
        await self._session.flush([user])

    async def check_command_exists(self, command_id: uuid.UUID) -> bool:
        """Check that the command exists."""
        stmt = select(exists().where(Command.id == command_id))
        result = await self._session.execute(stmt)
        return bool(result.scalar_one_or_none())
