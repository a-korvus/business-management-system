"""Unit Of Work project base implementation."""

import types
from typing import Self, Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from project.core.interfaces import AbsUnitOfWork, ModelType


class BaseSAUnitOfWork(AbsUnitOfWork[ModelType]):
    """Unit of work implementation using SQLAlchemy."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        """Initialize the unit of work."""
        if not any((session_factory, session)):
            raise ValueError(f"{self.__class__.__name__} has not session!")

        if all((session_factory, session)):
            raise ValueError(
                f"{self.__class__.__name__} must have either a "
                "'session_factory' or a 'session', not both!"
            )

        self._session_factory = session_factory
        self._external_session = session

        self._session: AsyncSession | None = session

    async def __aenter__(self) -> Self:
        """Enter to context manager. Create a session.

        Repositories in child objects need to be initialized.
        """
        if self._session_factory:
            self._session = self._session_factory()

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
        if not self._session:
            return

        try:
            if exc_type:
                await self.rollback()
        finally:
            if self._session_factory:
                await self._session.close()
                self._session = None

    async def commit(self) -> None:
        """Commit the current transaction."""
        if not self._session:
            raise RuntimeError("Session is not active for commit.")

        try:
            await self._session.commit()
        except Exception:  # noqa
            await self.rollback()
            raise

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

    async def flush(
        self,
        instances: Sequence[ModelType] | None = None,
    ) -> None:
        """Flush the current session objects."""
        if not self._session:
            raise RuntimeError("Session is not active for flush.")

        await self._session.flush(instances)
