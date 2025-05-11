"""Dependencies in the 'app_team' app."""

from typing import Annotated

from fastapi import Depends

from project.app_team.application.services.task import TaskService
from project.app_team.application.services.task_comment import (
    TaskCommentService,
)
from project.app_team.infrastructure.unit_of_work import SATeamUnitOfWork
from project.core.db.setup import AsyncSessionFactory
from project.core.log_config import get_logger

logger = get_logger(__name__)


def get_uof() -> SATeamUnitOfWork:
    """Get 'app_team' Unit of Work instance."""
    return SATeamUnitOfWork(session_factory=AsyncSessionFactory)


def get_task_service(
    uow: Annotated[SATeamUnitOfWork, Depends(get_uof)],
) -> TaskService:
    """Get TaskService instance."""
    return TaskService(uow=uow)


def get_taskcomment_service(
    uow: Annotated[SATeamUnitOfWork, Depends(get_uof)],
) -> TaskCommentService:
    """Get TaskCommentService instance."""
    return TaskCommentService(uow=uow)
