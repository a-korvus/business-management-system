"""Departments router in the 'app_org'."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from project.app_org.application.schemas import (
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
)
from project.app_org.application.services.department import DepartmentService
from project.app_org.domain.exceptions import DepartmentNotFound
from project.app_org.domain.models import Department
from project.app_org.presentation.dependencies import get_department_service
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix=f"{settings.PREFIX_ORG}/departments",
    tags=["org", "departments"],
)


@router.post(
    path="/",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new department.",
    description="Create a new department in the organization.",
)
async def create_department(
    data: DepartmentCreate,
    department_service: Annotated[
        DepartmentService, Depends(get_department_service)
    ],
) -> Department:
    """Create a new Department."""
    try:
        return await department_service.create(data)
    except ValueError as e:  # ошибки валидации из домена
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:  # любые непредвиденные ошибки # noqa
        logger.exception("Unexpected error while creating new department.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while creating new department.",
        )


@router.get(
    path="/",
    response_model=list[DepartmentRead],
    status_code=status.HTTP_200_OK,
    summary="Get departments.",
    description="Get all departments in the organization.",
)
async def get_departments(
    department_service: Annotated[
        DepartmentService, Depends(get_department_service)
    ],
) -> list[Department]:
    """Get all departments."""
    try:
        return await department_service.get_all()
    except Exception:  # noqa
        logger.exception("Unexpected error while retrieving all departments.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while retrieving "
            "all departments.",
        )


@router.get(
    path="/{department_id}/",
    response_model=DepartmentRead,
    status_code=status.HTTP_200_OK,
    summary="Get the department.",
    description="Get the specific department by its ID.",
)
async def get_specific_department(
    department_id: uuid.UUID,
    department_service: Annotated[
        DepartmentService, Depends(get_department_service)
    ],
) -> Department | None:
    """Get the Department by ID."""
    try:
        return await department_service.get_by_id(department_id)
    except Exception:  # noqa
        logger.exception("Unexpected error while retrieving the department.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while retrieving "
            "the department.",
        )


@router.put(
    path="/{department_id}/",
    response_model=DepartmentRead,
    status_code=status.HTTP_200_OK,
    summary="Update department.",
    description="Update the department data by its ID.",
)
async def update_department(
    department_id: uuid.UUID,
    updating_data: DepartmentUpdate,
    department_service: Annotated[
        DepartmentService, Depends(get_department_service)
    ],
) -> Department:
    """Update the Department by ID."""
    try:
        return await department_service.update(
            department_id=department_id,
            data=updating_data,
        )
    except DepartmentNotFound as e:
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
        logger.exception("Unexpected error while updating the department.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while updating the department.",
        )
