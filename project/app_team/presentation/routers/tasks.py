"""Tasks router in the 'app_team'."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse

from project.app_auth.application.schemas import TokenData
from project.app_auth.domain.exceptions import UserNotFound
from project.app_auth.presentation.dependencies import get_current_user_data
from project.app_team.application.schemas import (
    Period,
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
from project.app_team.domain.exceptions import (
    CalendarEventNotFound,
    TaskNotFound,
)
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
    except CalendarEventNotFound as e:
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
    except CalendarEventNotFound as e:
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


@router.get(
    path="/me/",
    response_model=list[TaskRead],
    status_code=status.HTTP_200_OK,
)
async def assigned_tasks(
    period_schema: Annotated[Period, Depends()],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    token_data: Annotated[TokenData, Depends(get_current_user_data)],
) -> list[Task]:
    """Get tasks assigned to a user for a period."""
    try:
        return await task_service.get_assigned_tasks(
            assignee_id=uuid.UUID(token_data.uid),
            period=period_schema,
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while receiving assigned task.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while receiving assigned task.",
        )


@router.get(
    path="/me/grades/",
    status_code=status.HTTP_200_OK,
)
async def grades_assigned_tasks(
    period_schema: Annotated[Period, Depends()],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    token_data: Annotated[TokenData, Depends(get_current_user_data)],
) -> list[tuple[str, int]]:
    """Get user tasks grades for a period.

    Tasks without a grade are not displayed.
    """
    try:
        return await task_service.get_grades_assigned_tasks(
            assignee_id=uuid.UUID(token_data.uid),
            period=period_schema,
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while receiving user grades.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while receiving user grades.",
        )


@router.get(
    path="/me/grades/avg/",
    status_code=status.HTTP_200_OK,
)
async def avg_grade_period(
    period_schema: Annotated[Period, Depends()],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    token_data: Annotated[TokenData, Depends(get_current_user_data)],
) -> ORJSONResponse:
    """Get average user grade for a specified period."""
    try:
        avg_grade = await task_service.get_avg_grade_period(
            assignee_id=uuid.UUID(token_data.uid),
            period=period_schema,
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while receiving user avg grade.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while receiving user avg grade.",
        )

    if not avg_grade:
        return ORJSONResponse(content={"avg_grade": "no data"})
    return ORJSONResponse(content={"avg_grade": str(avg_grade)})


@router.get(
    path="/me/grades/avg/command/",
    status_code=status.HTTP_200_OK,
)
async def avg_grade_period_command(
    period_schema: Annotated[Period, Depends()],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    token_data: Annotated[TokenData, Depends(get_current_user_data)],
) -> ORJSONResponse:
    """Get average grade of user command for a specified period."""
    try:
        command_avg_grade = await task_service.get_avg_grade_period_command(
            assignee_id=uuid.UUID(token_data.uid),
            period=period_schema,
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected error while receiving command avg grade.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while receiving command avg grade.",
        )

    if not command_avg_grade:
        return ORJSONResponse(content={"command_avg_grade": "no data"})
    return ORJSONResponse(
        content={"command_avg_grade": str(command_avg_grade)}
    )
