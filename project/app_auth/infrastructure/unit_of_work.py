"""Unit of work actions in the 'app_auth' app."""

from typing import Self

from project.app_auth.infrastructure.repositories import SAUserRepository
from project.core.unit_of_work import BaseSAUnitOfWork


class SAAuthUnitOfWork(BaseSAUnitOfWork):
    """Unit of work implementation. Applicable to the 'app_auth'."""

    users: SAUserRepository

    async def __aenter__(self) -> Self:
        """Create a session in the parent object. Initialize repositories."""
        await super().__aenter__()

        self.users = SAUserRepository(self._session)

        return self
