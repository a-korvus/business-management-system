"""Calendar event router in the 'app_team'."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from project.app_team.application.schemas import (
    CalendarEventCreate,
    CalendarEventRead,
    Period,
    UserToEvent,
)
from project.app_team.application.services.calendar_events import (
    CalendarEventService,
)
from project.app_team.domain.exceptions import (
    CalendarEventNotFound,
    OverlapError,
)
from project.app_team.domain.models import CalendarEvent
from project.app_team.presentation.dependencies import get_event_service
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix=f"{settings.PREFIX_TEAM}/events",
    tags=["team", "events"],
)


@router.post(
    path="/",
    response_model=CalendarEventRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    data: CalendarEventCreate,
    event_service: Annotated[CalendarEventService, Depends(get_event_service)],
) -> CalendarEvent:
    """Create a calendar event."""
    try:
        return await event_service.create_event(data)
    except Exception as e:  # noqa
        logger.exception("Unexpected error while creating an event.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while creating an event.",
        )


@router.get(
    path="/",
    response_model=list[CalendarEventRead],
    status_code=status.HTTP_200_OK,
)
async def get_events_period(
    period_schema: Annotated[Period, Depends()],
    event_service: Annotated[CalendarEventService, Depends(get_event_service)],
) -> list[CalendarEvent]:
    """Get all calendar events for a period."""
    try:
        return await event_service.list_for_period(period_schema)
    except Exception as e:  # noqa
        logger.exception("Unexpected error while receiving a list of events.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while receiving a list of events.",
        )


@router.patch(
    path="/",
    response_model=CalendarEventRead,
    status_code=status.HTTP_200_OK,
)
async def include_user(
    data: UserToEvent,
    event_service: Annotated[CalendarEventService, Depends(get_event_service)],
) -> CalendarEvent:
    """Add users to the calendar event."""
    try:
        return await event_service.include_user(
            user_id=data.user_id,
            event_id=data.event_id,
        )
    except CalendarEventNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OverlapError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while including user to event.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while including user to event.",
        )
