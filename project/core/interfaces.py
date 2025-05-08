"""Infrastructure interfaces in this project."""

import abc
from types import TracebackType
from typing import Generic, Self, Sequence, TypeVar

from project.core.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class AbsUnitOfWork(abc.ABC, Generic[ModelType]):
    """Interface for implementing app-specific transaction management."""

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
    async def rollback(self) -> None:
        """Rollback changes within a session."""
        raise NotImplementedError

    @abc.abstractmethod
    async def refresh(
        self,
        instance: ModelType,
        attribute_names: Sequence[str] | None = None,
    ) -> None:
        """Refresh the given instance from the database."""
        raise NotImplementedError
