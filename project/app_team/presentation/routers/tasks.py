"""Tasks router in the 'app_team'."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from project.app_auth.domain.exceptions import UserNotFound
from project.app_team.application.schemas import (
    TaskCommentCreate,
    TaskCommentRead,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from project.app_team.application.services.task import TaskService
from project.app_team.application.services.task_comment import (
    TaskCommentService,
)
from project.app_team.domain.exceptions import TaskNotFound
from project.app_team.domain.models import Task, TaskComment
from project.app_team.presentation.dependencies import (
    get_task_service,
    get_taskcomment_service,
)
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix=f"{settings.PREFIX_TEAM}/tasks",
    tags=["team", "tasks"],
)


@router.post(
    path="/",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskRead,
)
async def create_task(
    data: TaskCreate,
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> Task:
    """Create and assign a task."""
    try:
        return await task_service.create_assignment(data)
    except UserNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while creating new task.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while creating new task.",
        )


@router.patch(
    path="/{task_id}/",
    status_code=status.HTTP_200_OK,
    response_model=TaskRead,
)
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> Task:
    """Update an existing task."""
    try:
        return await task_service.update_task(task_id, data)
    except TaskNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except UserNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while updating a task.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while updating a task.",
        )


@router.delete(path="/{task_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_task(
    task_id: uuid.UUID,
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> None:
    """Deacticate a task."""
    try:
        await task_service.deactivate_task(task_id)
    except TaskNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while deactivating a task.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while deactivating a task.",
        )


@router.post(
    path="/comments/",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskCommentRead,
)
async def create_comment(
    comment_data: TaskCommentCreate,
    taskcomment_service: Annotated[
        TaskCommentService,
        Depends(get_taskcomment_service),
    ],
) -> TaskComment:
    """Write a comment to the task."""
    try:
        return await taskcomment_service.create_comment(comment_data)
    except TaskNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except UserNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while creating a comment.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while creating a comment.",
        )
