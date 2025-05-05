"""Unit of work actions in the 'app_auth' app."""

import types
from typing import Self, Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from project.app_auth.application.interfaces import (
    AbstractUnitOfWork,
    ModelType,
)
from project.app_auth.infrastructure.repositories import SAUserRepository


class SAUnitOfWork(AbstractUnitOfWork):
    """Unit of work implementation using SQLAlchemy."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        """Initialize the unit of work."""
        if session_factory is None and session is None:
            raise ValueError(f"{self.__class__.__name__} has not session!")

        if session_factory and session:
            raise ValueError(
                f"{self.__class__.__name__} must have either a "
                "session factory or a session, not both!"
            )

        self._session_factory = session_factory
        self._session = session

    async def __aenter__(self) -> Self:
        """Enter to context manager. Create a session and repositories."""
        if self._session_factory:
            self._session = self._session_factory()

        self.users = SAUserRepository(self._session)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit from context manager.

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

    async def refresh(
        self,
        instance: ModelType,
        attribute_names: Sequence[str] | None = None,
    ) -> None:
        """Refresh the given instance from the database."""
        if not self._session:
            raise RuntimeError("Session is not active for refresh.")

        try:
            await self._session.refresh(
                instance,
                attribute_names=attribute_names,
            )
        except Exception:  # noqa
            await self.rollback()
            raise

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if not self._session:
            raise RuntimeError("Session is not active for rollback.")

        await self._session.rollback()
