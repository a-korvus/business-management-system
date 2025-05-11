"""Pytest configuration settings for 'app_team' tests."""

from typing import Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_team.application.services.task import TaskService
from project.app_team.application.services.task_comment import (
    TaskCommentService,
)
from project.app_team.infrastructure.unit_of_work import SATeamUnitOfWork
from project.core.log_config import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="function")
def uow_factory(
    db_session: AsyncSession,
) -> Callable[[], SATeamUnitOfWork]:
    """Factory to create UoW instances using the same test session."""
    logger.debug("uow_factory created with db_session: '%d'", id(db_session))

    def _create_uow() -> SATeamUnitOfWork:
        logger.debug("New UoW created with db_session: '%d'", id(db_session))
        return SATeamUnitOfWork(session=db_session)

    return _create_uow


@pytest.fixture(scope="function")
def verify_task_service(
    uow_factory: Callable[[], SATeamUnitOfWork],
) -> TaskService:
    """Get task service instance."""
    return TaskService(uow_factory())


@pytest.fixture(scope="function")
def verify_taskcomment_service(
    uow_factory: Callable[[], SATeamUnitOfWork],
) -> TaskCommentService:
    """Get task comment service instance."""
    return TaskCommentService(uow_factory())
