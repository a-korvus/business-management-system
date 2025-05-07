"""Roles router in the 'app_org'."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from project.app_auth.domain.models import User
from project.app_auth.presentation.dependencies import get_admin
from project.app_org.application.schemas import (
    RoleCreate,
    RoleRead,
    RoleUpdate,
)
from project.app_org.application.services.role import RoleService
from project.app_org.domain.exceptions import RoleNotEmpty, RoleNotFound
from project.app_org.domain.models import Role
from project.app_org.presentation.dependencies import get_role_service
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix=f"{settings.PREFIX_ORG}/roles",
    tags=["org", "roles"],
)


@router.post(
    path="/",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role.",
    description="Create a new role in the organization.",
)
async def create_role(
    data: RoleCreate,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    admin: Annotated[User, Depends(get_admin)],
) -> Role:
    """Create a new Role. Protected. For admins only."""
    try:
        return await role_service.create(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while creating new role.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while creating new role.",
        )


@router.get(
    path="/",
    response_model=list[RoleRead],
    status_code=status.HTTP_200_OK,
    summary="Get roles.",
    description="Get all roles in the organization.",
)
async def get_roles(
    role_service: Annotated[RoleService, Depends(get_role_service)],
) -> list[Role]:
    """Get all roles."""
    try:
        return await role_service.get_all()
    except Exception:  # noqa
        logger.exception("Unexpected error while retrieving all roles.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while retrieving all roles.",
        )


@router.get(
    path="/{role_id}/",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Get the role.",
    description="Get the specific role by its ID.",
)
async def get_specific_role(
    role_id: uuid.UUID,
    role_service: Annotated[RoleService, Depends(get_role_service)],
) -> Role | None:
    """Get the Role by ID."""
    try:
        return await role_service.get_by_id(role_id)
    except Exception:  # noqa
        logger.exception("Unexpected error while retrieving the post.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while retrieving the post.",
        )


@router.put(
    path="/{role_id}/",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Update role.",
    description="Update the role data by its ID.",
)
async def update_role(
    role_id: uuid.UUID,
    updating_data: RoleUpdate,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    admin: Annotated[User, Depends(get_admin)],
) -> Role:
    """Update the Role by ID. Protected. For admins only."""
    try:
        return await role_service.update(role_id=role_id, data=updating_data)
    except RoleNotFound as e:
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
        logger.exception("Unexpected error while updating the role.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while updating the role.",
        )


@router.delete(
    path="/{role_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate role.",
)
async def deactivate_role(
    role_id: uuid.UUID,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    admin: Annotated[User, Depends(get_admin)],
) -> None:
    """Deactivate the Role by ID. Protected. For admins only."""
    try:
        await role_service.deactivate(role_id=role_id)
    except RoleNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RoleNotEmpty as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception:  # noqa
        logger.exception("Unexpected error while deactivating the role.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while deactivating the role.",
        )


@router.post(
    path="/{role_id}/activate/",
    status_code=status.HTTP_200_OK,
    summary="Activate role.",
)
async def activate_role(
    role_id: uuid.UUID,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    admin: Annotated[User, Depends(get_admin)],
) -> None:
    """Activate the Role by ID. Protected. For admins only."""
    try:
        await role_service.activate(role_id)
    except RoleNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception:  # noqa
        logger.exception("Unexpected error while activating the role.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while activating the role.",
        )
