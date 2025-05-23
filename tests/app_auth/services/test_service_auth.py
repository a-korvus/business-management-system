"""Test AuthService from 'app_auth' app."""

from typing import Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.application.interfaces import PasswordHasher
from project.app_auth.application.schemas import (
    LoginSchema,
    Token,
    UserCreate,
    UserRead,
)
from project.app_auth.application.services.auth import AuthService
from project.app_auth.domain.models import Profile, User
from project.app_auth.infrastructure.unit_of_work import SAAuthUnitOfWork


def test_true() -> None:
    """Run simple check test."""
    assert True


@pytest.mark.usefixtures("truncate_tables")
@pytest.mark.anyio
async def test_register_user(
    verify_auth_service: AuthService,
    uow_factory: Callable[[], SAAuthUnitOfWork],
    fake_user_schema: UserCreate,
    fake_hasher: PasswordHasher,
) -> None:
    """Test successful user registration."""
    new_user_schema: UserRead = await verify_auth_service.register_user(
        user_data=fake_user_schema,
    )

    # проверяем возвращенную схему
    assert isinstance(new_user_schema, UserRead)
    assert new_user_schema.email == fake_user_schema.email
    assert new_user_schema.id is not None
    assert new_user_schema.is_active is True

    # проверяем данные в фейковом репозитории через UoW
    async with uow_factory() as uow:  # через UoW получаем доступ к репозиторию
        saved_user = await uow.users.get_by_email(
            email=fake_user_schema.email,
        )

    assert isinstance(saved_user, User)
    assert saved_user.email == fake_user_schema.email
    assert saved_user.id == new_user_schema.id
    assert saved_user.hashed_password == fake_hasher.hash_password(
        fake_user_schema.password
    )

    assert isinstance(saved_user.profile, Profile)
    assert saved_user.profile.first_name is None
    assert saved_user.profile.last_name is None
    assert saved_user.profile.bio is None


@pytest.mark.anyio
async def test_authenticate_user(
    verify_auth_service: AuthService,
    fake_user_schema: UserCreate,
    fake_hasher: PasswordHasher,
    db_session: AsyncSession,
) -> None:
    """Test successful user authentication."""
    new_user = User(
        email=fake_user_schema.email,
        plain_password=fake_user_schema.password,
        hasher=fake_hasher,
    )
    db_session.add(new_user)
    await db_session.commit()

    login_schema = LoginSchema(
        username=fake_user_schema.email,
        password=fake_user_schema.password,
    )
    token = await verify_auth_service.authenticate_user(login_schema)

    assert isinstance(token, Token)
    assert token.token_type == "bearer"
