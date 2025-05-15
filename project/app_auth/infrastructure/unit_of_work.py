"""Unit of work implementation for the 'app_auth' app."""

from typing import Self

from project.app_auth.infrastructure.repositories import SAUserRepository
from project.core.unit_of_work import BaseSAUnitOfWork


class SAAuthUnitOfWork(BaseSAUnitOfWork):
    """Unit of work implementation. Applicable to the 'app_auth'."""

    users: SAUserRepository

    async def __aenter__(self) -> Self:
        """Create a session in the parent object. Initialize repositories."""
        await super().__aenter__()

        if self._session is None:
            raise ValueError(f"{self.__class__.__name__} got an empty session")

        self.users = SAUserRepository(self._session)

        return self
