"""Meetings router in the 'app_team'."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from project.app_team.application.schemas import (
    MeetingCreate,
    MeetingRead,
    MeetingUpdate,
)
from project.app_team.application.services.meeting import MeetingService
from project.app_team.domain.exceptions import (
    MeetingNotFound,
    OverlapError,
)
from project.app_team.domain.models import Meeting
from project.app_team.presentation.dependencies import get_meeting_service
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix=f"{settings.PREFIX_TEAM}/meetings",
    tags=["team", "meetings"],
)


@router.post(
    path="/",
    status_code=status.HTTP_201_CREATED,
    response_model=MeetingRead,
)
async def create_meeting(
    data: MeetingCreate,
    meeting_service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> Meeting:
    """Create a new meeting."""
    try:
        return await meeting_service.create(data)
    except OverlapError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while creating a meeting.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while creating a meeting.",
        )


@router.patch(
    path="/{meeting_id}/",
    status_code=status.HTTP_200_OK,
    response_model=MeetingRead,
)
async def update_meeting(
    meeting_id: uuid.UUID,
    data: MeetingUpdate,
    meeting_service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> Meeting:
    """Update an existing meeting."""
    try:
        return await meeting_service.update(meeting_id, data)
    except MeetingNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while updating a meeting.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while updating a meeting.",
        )


@router.delete(
    path="/{meeting_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_meeting(
    meeting_id: uuid.UUID,
    meeting_service: Annotated[MeetingService, Depends(get_meeting_service)],
) -> None:
    """Deactivate a meeting."""
    try:
        await meeting_service.deactivate(meeting_id)
    except MeetingNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while deactivating a meeting.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while deactivating a meeting.",
        )


@router.patch(
    path="/{meeting_id}/include/",
    status_code=status.HTTP_200_OK,
    response_model=MeetingRead,
)
async def include_users(
    meeting_id: Annotated[uuid.UUID, Path(...)],
    meeting_service: Annotated[MeetingService, Depends(get_meeting_service)],
    user_ids: Annotated[list[uuid.UUID], Body(...)],
) -> Meeting:
    """Add new users to the meeting."""
    try:
        return await meeting_service.include_users(meeting_id, user_ids)
    except MeetingNotFound as e:
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
        logger.exception("Unexpected error while including users.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while including users.",
        )
