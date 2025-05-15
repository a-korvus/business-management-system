"""Pytest configuration settings for 'app_auth' tests."""

import random
from typing import Callable

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_org.application.enums import RoleType
from project.app_org.application.schemas import (
    CommandCreate,
    DepartmentCreate,
    NewsCreate,
    RoleCreate,
)
from project.app_org.application.services.command import CommandService
from project.app_org.application.services.dep_in_com import (
    DepartmentInCommandService,
)
from project.app_org.application.services.department import DepartmentService
from project.app_org.application.services.news import NewsService
from project.app_org.application.services.role import RoleService
from project.app_org.infrastructure.unit_of_work import SAOrgUnitOfWork
from project.core.db.setup import AsyncSessionFactory
from project.core.log_config import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="function")
def uow_sess_factory() -> Callable[[], SAOrgUnitOfWork]:
    """Factory to create UoW instance with project session factory."""
    logger.debug(
        "uow_factory created with session factory: '%d'",
        id(AsyncSessionFactory),
    )

    def _create_uow_session_factory() -> SAOrgUnitOfWork:
        logger.debug(
            "New UoW created with session factory: '%d'",
            id(AsyncSessionFactory),
        )
        return SAOrgUnitOfWork(session_factory=AsyncSessionFactory)

    return _create_uow_session_factory


@pytest.fixture(scope="function")
def uow_factory(
    db_session: AsyncSession,
) -> Callable[[], SAOrgUnitOfWork]:
    """Factory to create UoW instances using the same test session."""
    logger.debug("uow_factory created with db_session: '%d'", id(db_session))

    def _create_uow() -> SAOrgUnitOfWork:
        logger.debug("New UoW created with db_session: '%d'", id(db_session))
        return SAOrgUnitOfWork(session=db_session)

    return _create_uow


@pytest.fixture(scope="function")
def verify_command_service(
    uow_factory: Callable[[], SAOrgUnitOfWork],
) -> CommandService:
    """Get command service instance."""
    return CommandService(uow_factory())


@pytest.fixture(scope="function")
def verify_dep_in_com_service(
    uow_factory: Callable[[], SAOrgUnitOfWork],
) -> DepartmentInCommandService:
    """Get department in command service instance."""
    return DepartmentInCommandService(uow_factory())


@pytest.fixture(scope="function")
def verify_department_service(
    uow_factory: Callable[[], SAOrgUnitOfWork],
) -> DepartmentService:
    """Get department service instance."""
    return DepartmentService(uow_factory())


@pytest.fixture(scope="function")
def verify_role_service(
    uow_factory: Callable[[], SAOrgUnitOfWork],
) -> RoleService:
    """Get role service instance."""
    return RoleService(uow_factory())


@pytest.fixture(scope="function")
def verify_news_service(
    uow_factory: Callable[[], SAOrgUnitOfWork],
) -> NewsService:
    """Get news service instance."""
    return NewsService(uow_factory())


@pytest.fixture(scope="function")
def fake_command_schema(fake_instance: Faker) -> CommandCreate:
    """Define the fake Command for tests."""
    return CommandCreate(
        name=fake_instance.company(),
        description=fake_instance.text(max_nb_chars=500),
    )


@pytest.fixture(scope="function")
def fake_department_schema(fake_instance: Faker) -> DepartmentCreate:
    """Define the fake Department for tests."""
    return DepartmentCreate(
        name=fake_instance.company(),
        description=fake_instance.text(max_nb_chars=500),
    )


@pytest.fixture(scope="function")
def fake_role_schema(fake_instance: Faker) -> RoleCreate:
    """Define the fake Role for tests."""
    return RoleCreate(description=fake_instance.text(max_nb_chars=500))


@pytest.fixture(scope="function")
def fake_news_schema(fake_instance: Faker) -> NewsCreate:
    """Define the fake News for tests."""
    return NewsCreate(
        text=fake_instance.text(max_nb_chars=5000),
    )


@pytest.fixture(scope="function")
def fake_command_data(fake_instance: Faker) -> dict:
    """Define the data of some Command for tests."""
    return {
        "name": fake_instance.unique.company(),
        "description": fake_instance.text(max_nb_chars=500),
    }


@pytest.fixture(scope="function")
def fake_department_data(fake_instance: Faker) -> dict:
    """Define the data of some Department for tests."""
    return {
        "name": fake_instance.company(),
        "description": fake_instance.text(max_nb_chars=500),
    }


@pytest.fixture(scope="function")
def fake_role_data(fake_instance: Faker) -> dict:
    """Define the data of some Role for tests."""
    return {
        "name": random.choice(RoleType.get_values()),
        "description": fake_instance.text(max_nb_chars=500),
    }


@pytest.fixture(scope="function")
def fake_news_data(fake_instance: Faker) -> dict:
    """Define the data of some News post for tests."""
    return {
        "text": fake_instance.text(max_nb_chars=5000),
    }
