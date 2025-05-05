"""Pytest configuration settings for 'app_auth' tests."""

from typing import Any, Callable

import pytest
from faker import Faker
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.application.interfaces import (
    AbstractUnitOfWork,
    PasswordHasher,
)
from project.app_auth.application.schemas import UserCreate
from project.app_auth.application.services import AuthService, UserService
from project.app_auth.infrastructure.unit_of_work import SAUnitOfWork
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)

AUTH_PREFIX = settings.AUTH.PREFIX_AUTH


class FakePasswordHasher(PasswordHasher):
    """Test implementation of password hasher."""

    def hash_password(self, plain_pswrd: str) -> str:
        """Encrypt the password."""
        return f"hashed_{plain_pswrd}"

    def verify_password(self, plain_pswrd: str, stored_pswrd: str) -> bool:
        """Verify plain password is an encrypted password."""
        return stored_pswrd == f"hashed_{plain_pswrd}"


@pytest.fixture(scope="session")
def fake_hasher() -> FakePasswordHasher:
    """One password hasher for the all tests."""
    return FakePasswordHasher()


@pytest.fixture(scope="function")
def fake_user_schema(fake_instance: Faker) -> UserCreate:
    """Define the fake user for tests."""
    return UserCreate(
        email=fake_instance.email(),
        password=fake_instance.password(),
    )


@pytest.fixture(scope="function")
def uow_factory(
    db_session: AsyncSession,
) -> Callable[[], AbstractUnitOfWork]:
    """Factory to create UoW instances using the same test session."""
    logger.debug("uow_factory created with db_session: '%d'", id(db_session))

    def _create_uow() -> AbstractUnitOfWork:
        logger.debug("New UoW created with db_session: '%d'", id(db_session))
        return SAUnitOfWork(session=db_session)

    return _create_uow


@pytest.fixture(scope="function")
def verify_auth_service(
    uow_factory: Callable[[], AbstractUnitOfWork],
    fake_hasher: PasswordHasher,
) -> AuthService:
    """Get authentication service instance."""
    uow_instance = uow_factory()
    return AuthService(
        uow=uow_instance,
        hasher=fake_hasher,
    )


@pytest.fixture(scope="function")
def verify_user_service(
    uow_factory: Callable[[], AbstractUnitOfWork],
) -> UserService:
    """Get user service instance."""
    return UserService(uow=uow_factory())


async def get_auth_token(
    httpx_client: AsyncClient,
    email: str,
    password: str,
) -> str:
    """Get authentication token."""
    response = await httpx_client.post(
        url=f"{AUTH_PREFIX}/login/",
        data={"username": email, "password": password},
    )
    response.raise_for_status()
    return response.json()["access_token"]


@pytest.fixture(scope="function")
async def authenticated_user(
    httpx_test_client: AsyncClient,
    fake_user_schema: UserCreate,
) -> dict[str, Any]:
    """Create new user and return this user data."""
    response: Response = await httpx_test_client.post(
        url=f"{AUTH_PREFIX}/register/", json=fake_user_schema.model_dump()
    )
    assert response.status_code == 201

    new_user_data: dict = response.json()
    token = await get_auth_token(
        httpx_client=httpx_test_client,
        email=fake_user_schema.email,
        password=fake_user_schema.password,
    )

    return {"user": new_user_data, "token": token}
