"""CalendarEvent-related service in 'app_team'."""

import uuid

from project.app_auth.domain.exceptions import UserNotFound
from project.app_team.application.schemas import CalendarEventCreate, Period
from project.app_team.domain.exceptions import (
    CalendarEventNotFound,
    OverlapError,
)
from project.app_team.domain.models import CalendarEvent
from project.app_team.infrastructure.unit_of_work import SATeamUnitOfWork
from project.core.log_config import get_logger

logger = get_logger(__name__)


class CalendarEventService:
    """Application service for managing calendar events."""

    def __init__(self, uow: SATeamUnitOfWork) -> None:
        """Initialize the service object. Set UoW."""
        self.uow = uow
        logger.debug("'%s' initialized", self.__class__.__name__)

    async def get_by_id(self, event_id: uuid.UUID) -> CalendarEvent | None:
        """Get calendar event by ID."""
        async with self.uow as uow:
            return await uow.events.get_by_id(event_id)

    async def create_event(self, data: CalendarEventCreate) -> CalendarEvent:
        """Create a new calendar event."""
        async with self.uow as uow:
            new_event = CalendarEvent(**data.model_dump())
            await uow.events.add(new_event)
            await uow.commit()

            return new_event

    async def list_for_period(self, period: Period) -> list[CalendarEvent]:
        """Get all calendar events for a specified period."""
        async with self.uow as uow:
            return await uow.events.list_all_period(
                start_date=period.start,
                end_date=period.end,
            )

    async def include_user(
        self,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
    ) -> CalendarEvent:
        """Include the user in the calendar event."""
        async with self.uow as uow:
            user = await uow.partners.get_by_id(user_id)
            if not user:
                raise UserNotFound(user_id=user_id)

            event = await self.uow.events.get_by_id_detail(event_id)
            if not event:
                raise CalendarEventNotFound(event_id)

            overlap = await uow.events.check_overlap_users(
                start_time=event.start_time,
                end_time=event.end_time,
                user_ids={user_id},
                event_id=event_id,
            )
            if overlap:
                raise OverlapError(event_id)

            event.users.append(user)
            await uow.commit()

            return event
