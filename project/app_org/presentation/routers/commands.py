"""Commands router in the 'app_org'."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from project.app_org.application.schemas import (
    CommandCreate,
    CommandRead,
    CommandUpdate,
)
from project.app_org.application.services.command import CommandService
from project.app_org.domain.exceptions import CommandNotFound
from project.app_org.domain.models import Command
from project.app_org.presentation.dependencies import get_command_service
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix=f"{settings.PREFIX_ORG}/commands",
    tags=["org", "commands"],
)


@router.post(
    path="/",
    response_model=CommandRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new command.",
    description="Create a new command in the organization.",
)
async def create_command(
    data: CommandCreate,
    command_service: Annotated[CommandService, Depends(get_command_service)],
) -> Command:
    """Create a new Command."""
    try:
        return await command_service.create(data)
    except ValueError as e:  # ошибки валидации из домена
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:  # любые непредвиденные ошибки # noqa
        logger.exception("Unexpected error while creating new command.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while creating new command.",
        )


@router.get(
    path="/",
    response_model=list[CommandRead],
    status_code=status.HTTP_200_OK,
    summary="Get commands.",
    description="Get all commands in the organization.",
)
async def get_commands(
    command_service: Annotated[CommandService, Depends(get_command_service)],
) -> list[Command]:
    """Get all commands."""
    try:
        return await command_service.get_all()
    except Exception:  # noqa
        logger.exception("Unexpected error while retrieving all commands.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while retrieving all commands.",
        )


@router.get(
    path="/{command_id}/",
    response_model=CommandRead,
    status_code=status.HTTP_200_OK,
    summary="Get the command.",
    description="Get the specific command by its ID.",
)
async def get_specific_command(
    command_id: uuid.UUID,
    command_service: Annotated[CommandService, Depends(get_command_service)],
) -> Command | None:
    """Get the Command by ID."""
    try:
        return await command_service.get_by_id(command_id)
    except Exception:  # noqa
        logger.exception("Unexpected error while retrieving the command.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while retrieving the command.",
        )


@router.put(
    path="/{command_id}/",
    response_model=CommandRead,
    status_code=status.HTTP_200_OK,
    summary="Update command.",
    description="Update the command data by its ID.",
)
async def update_command(
    command_id: uuid.UUID,
    updating_data: CommandUpdate,
    command_service: Annotated[CommandService, Depends(get_command_service)],
) -> Command:
    """Update the Command by ID."""
    try:
        return await command_service.update(
            command_id=command_id,
            data=updating_data,
        )
    except CommandNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:  # ошибки валидации
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:  # noqa
        logger.exception("Unexpected error while updating the command.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while updating the command.",
        )
