"""Repository interfaces in the 'app_auth' app."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from project.app_auth.application.interfaces import AbstractUserRepository
from project.app_auth.domain.models import User


class SAUserRepository(AbstractUserRepository):
    """Implementation of user repository using sqlalchemy."""

    def __init__(self, session: AsyncSession | None) -> None:
        """Initialize a User Repository."""
        if session is None:
            raise ValueError(f"{self.__class__.__name__} get an empty session")

        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get the user by ID. Load related profile."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get the user by email. Load related profile."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.email == email)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[User]:
        """Get all users."""
        stmt = select(User).options(selectinload(User.profile))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, user: User) -> None:
        """Add new user in sqlalchemy async session."""
        self._session.add(user)
