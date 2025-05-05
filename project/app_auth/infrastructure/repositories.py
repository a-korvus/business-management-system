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

    def __init__(self, session: AsyncSession | None) -> None:
        """Initialize a User Repository."""
        if session is None:
            raise ValueError(f"{self.__class__.__name__} get an empty session")

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

    async def list_all(self) -> list[User]:
        """Get all users."""
        result = await self._session.execute(select(User))
        return list(result.scalars().all())

    async def add(self, user: User) -> None:
        """Add new user in sqlalchemy async session."""
        self._session.add(user)

    async def check_command_exists(self, command_id: uuid.UUID) -> bool:
        """Check that the command exists."""
        stmt = select(exists().where(Command.id == command_id))
        result = await self._session.execute(stmt)
        return result.scalar_one()
