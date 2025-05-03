"""Dependencies in the 'app_org' app."""

from typing import Annotated

from fastapi import Depends

from project.app_org.application.interfaces import AbsUnitOfWork
from project.app_org.application.services.command import CommandService
from project.app_org.application.services.department import DepartmentService
from project.app_org.application.services.news import NewsService
from project.app_org.application.services.role import RoleService
from project.app_org.infrastructure.unit_of_work import SAOrgUnitOfWork
from project.core.db.setup import AsyncSessionFactory
from project.core.log_config import get_logger

logger = get_logger(__name__)


def get_uow() -> AbsUnitOfWork:
    """Get Unit of Work instance."""
    return SAOrgUnitOfWork(session_factory=AsyncSessionFactory)


def get_command_service(
    uow: Annotated[AbsUnitOfWork, Depends(get_uow)],
) -> CommandService:
    """Get CommandService instance."""
    return CommandService(uow=uow)


def get_department_service(
    uow: Annotated[AbsUnitOfWork, Depends(get_uow)],
) -> DepartmentService:
    """Get DepartmentService instance."""
    return DepartmentService(uow=uow)


def get_role_service(
    uow: Annotated[AbsUnitOfWork, Depends(get_uow)],
) -> RoleService:
    """Get RoleService instance."""
    return RoleService(uow=uow)


def get_news_service(
    uow: Annotated[AbsUnitOfWork, Depends(get_uow)],
) -> NewsService:
    """Get NewsService instance."""
    return NewsService(uow=uow)
