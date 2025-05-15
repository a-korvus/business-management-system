"""Unit of work implementation for the 'app_org' app."""

from typing import Self

from project.app_org.infrastructure.repos import (
    SACommandRepo,
    SADepartmentRepo,
    SANewsRepo,
    SARoleRepo,
)
from project.core.unit_of_work import BaseSAUnitOfWork


class SAOrgUnitOfWork(BaseSAUnitOfWork):
    """Unit of work implementation using SQLAlchemy."""

    commands: SACommandRepo
    departments: SADepartmentRepo
    roles: SARoleRepo
    news: SANewsRepo

    async def __aenter__(self) -> Self:
        """Create a session in the parent object. Initialize repositories."""
        await super().__aenter__()

        if self._session is None:
            raise ValueError(f"{self.__class__.__name__} got an empty session")

        self.commands = SACommandRepo(self._session)
        self.departments = SADepartmentRepo(self._session)
        self.roles = SARoleRepo(self._session)
        self.news = SANewsRepo(self._session)

        return self
