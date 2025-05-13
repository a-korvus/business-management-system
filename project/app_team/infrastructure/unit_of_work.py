"""Unit of work implementation for the 'app_team' app."""

from typing import Self

from project.app_team.infrastructure.repos import (
    SACalendarEventRepo,
    SAMeetingRepo,
    SAPartnerRepo,
    SATaskCommentRepo,
    SATaskRepo,
)
from project.core.unit_of_work import BaseSAUnitOfWork


class SATeamUnitOfWork(BaseSAUnitOfWork):
    """Unit of work implementation using SQLAlchemy."""

    partners: SAPartnerRepo
    tasks: SATaskRepo
    tasks_comments: SATaskCommentRepo
    events: SACalendarEventRepo
    meetings: SAMeetingRepo

    async def __aenter__(self) -> Self:
        """Create a session in the parent object. Initialize repositories."""
        await super().__aenter__()

        self.partners = SAPartnerRepo(self._session)
        self.tasks = SATaskRepo(self._session)
        self.tasks_comments = SATaskCommentRepo(self._session)
        self.events = SACalendarEventRepo(self._session)
        self.meetings = SAMeetingRepo(self._session)

        return self
