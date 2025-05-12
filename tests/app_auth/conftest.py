"""Pytest configuration settings for 'app_auth' tests."""

from typing import Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.application.interfaces import PasswordHasher
from project.app_auth.application.services.auth import AuthService
from project.app_auth.application.services.users import UserService
from project.app_auth.infrastructure.unit_of_work import SAAuthUnitOfWork
from project.core.log_config import get_logger

logger = get_logger(__name__)


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
def uow_factory(
    db_session: AsyncSession,
) -> Callable[[], SAAuthUnitOfWork]:
    """Factory to create UoW instances using the same test session."""
    logger.debug("uow_factory created with db_session: '%d'", id(db_session))

    def _create_uow() -> SAAuthUnitOfWork:
        logger.debug("New UoW created with db_session: '%d'", id(db_session))
        return SAAuthUnitOfWork(session=db_session)

    return _create_uow


@pytest.fixture(scope="function")
def verify_auth_service(
    uow_factory: Callable[[], SAAuthUnitOfWork],
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
    uow_factory: Callable[[], SAAuthUnitOfWork],
) -> UserService:
    """Get user service instance."""
    return UserService(uow=uow_factory())
