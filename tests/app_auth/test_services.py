"""Test services in the 'app_auth' app."""

from typing import Callable

import pytest

from project.app_auth.application.interfaces import (
    AbstractUnitOfWork,
    PasswordHasher,
)
from project.app_auth.application.schemas import UserCreate, UserRead
from project.app_auth.application.services import AuthService


def test_true() -> None:
    """Run simple check test."""
    assert True


# @pytest.mark.usefixtures("truncate_tables")
@pytest.mark.anyio
async def test_register_user_success(
    get_test_auth_service: AuthService,
    uow_factory: Callable[[], AbstractUnitOfWork],
    fake_hasher: PasswordHasher,
) -> None:
    """Тест успешной регистрации пользователя."""
    user_data = UserCreate(email="test@example.com", password="password123")

    created_user_schema = await get_test_auth_service.register_user(user_data)

    # проверяем возвращенную схему
    assert isinstance(created_user_schema, UserRead)
    assert created_user_schema.email == user_data.email
    assert created_user_schema.id is not None
    assert created_user_schema.is_active is True

    # проверяем данные в фейковом репозитории через UoW
    verify_uow = uow_factory()
    async with verify_uow:  # через UoW получаем доступ к репозиторию
        saved_user = await verify_uow.users.get_by_email(user_data.email)
        assert saved_user is not None
        assert saved_user.email == user_data.email
        assert saved_user.id == created_user_schema.id
        assert saved_user.hashed_password == fake_hasher.hash_password(
            user_data.password
        )
