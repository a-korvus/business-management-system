"""Unit of work actions in the 'app_auth' app."""

import types
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from project.app_auth.application.interfaces import AbstractUnitOfWork
from project.app_auth.infrastructure.repositories import SAUserRepository
from project.core.db.setup import AsyncSessionFactory


class SAUnitOfWork(AbstractUnitOfWork):
    """Unit of work implementation using SQLAlchemy."""

    def __init__(
        self,
        session_factory: async_sessionmaker[
            AsyncSession
        ] = AsyncSessionFactory,
    ) -> None:
        """Initialize the unit of work."""
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        """Enter to the context manager. Create a session and repositories."""
        self._session = self._session_factory()
        self.users = SAUserRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """
        Exit context manager.

        Rollback if error occurs. Close session anyway.
        """
        if self._session:
            if exc_type:
                await self.rollback()  # откат при ЛЮБОЙ ошибке
            await self._session.close()  # закрыть сессию в любом случае
            self._session = None

    async def commit(self) -> None:
        """Commit the current transaction."""
        if not self._session:
            raise RuntimeError("Session is not active for commit.")

        try:
            await self._session.commit()
        except Exception:  # noqa
            await self.rollback()  # откат при ЛЮБОЙ ошибке коммита
            raise  # проброс исключения выше

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if not self._session:
            raise RuntimeError("Session is not active for rollback.")

        await self._session.rollback()
