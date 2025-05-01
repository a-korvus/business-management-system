"""Test UserService from 'app_auth' app."""

import random
from typing import Callable

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.application.interfaces import (
    AbstractUnitOfWork,
    PasswordHasher,
)
from project.app_auth.application.schemas import (
    ProfileRead,
    ProfileUpdate,
    UserCreate,
    UserRead,
)
from project.app_auth.application.services import AuthService, UserService
from project.app_auth.domain.models import User


@pytest.mark.usefixtures("truncate_tables")
@pytest.mark.anyio
async def test_get_user_by_id(
    verify_auth_service: AuthService,
    verify_user_service: UserService,
    fake_user_schema: UserCreate,
) -> None:
    """Test successful getting user by ID."""
    created_user_schema: UserRead = await verify_auth_service.register_user(
        user_data=fake_user_schema,
    )
    user: User | None = await verify_user_service.get_user_by_id(
        user_id=created_user_schema.id,
    )

    assert isinstance(user, User)
    assert user.id == created_user_schema.id
    assert user.email == created_user_schema.email


@pytest.mark.usefixtures("truncate_tables")
@pytest.mark.anyio
async def test_get_user_by_email(
    verify_user_service: UserService,
    fake_user_schema: UserCreate,
    fake_hasher: PasswordHasher,
    db_session: AsyncSession,
) -> None:
    """Test successful getting user by email."""
    new_user = User(
        email=fake_user_schema.email,
        plain_password=fake_user_schema.password,
        hasher=fake_hasher,
    )
    db_session.add(new_user)
    await db_session.commit()

    user: User | None = await verify_user_service.get_user_by_email(
        email=fake_user_schema.email,
    )

    assert isinstance(user, User)
    assert user.email == fake_user_schema.email


@pytest.mark.usefixtures("truncate_tables")
@pytest.mark.anyio
async def test_get_all_users(
    verify_user_service: UserService,
    fake_user_schema: UserCreate,
    fake_hasher: PasswordHasher,
    db_session: AsyncSession,
) -> None:
    """Test successful getting list of all users."""
    schemas: list[UserCreate] = []
    for i in range(random.randint(15, 30)):
        schemas.append(
            UserCreate(
                email=str(i) + fake_user_schema.email,
                password=fake_user_schema.password + str(i),
            )
        )
    users: list[User] = [
        User(schema.email, schema.password, hasher=fake_hasher)
        for schema in schemas
    ]
    db_session.add_all(users)
    await db_session.commit()

    stored_users = await verify_user_service.get_all_users()

    assert isinstance(stored_users, list)
    assert len(users) == len(stored_users)
    for stored_user in stored_users:
        assert isinstance(stored_user, UserRead)


@pytest.mark.usefixtures("truncate_tables")
@pytest.mark.anyio
async def test_deactivate_activate_user(
    verify_user_service: UserService,
    uow_factory: Callable[[], AbstractUnitOfWork],
    fake_user_schema: UserCreate,
    fake_hasher: PasswordHasher,
    db_session: AsyncSession,
) -> None:
    """Test change user status."""
    new_user = User(
        email=fake_user_schema.email,
        plain_password=fake_user_schema.password,
        hasher=fake_hasher,
    )
    db_session.add(new_user)
    await db_session.commit()

    assert new_user.is_active is True

    change_status_deactivate = await verify_user_service.deactivate_user(
        user_id=new_user.id,
    )

    assert change_status_deactivate is True
    assert new_user.is_active is False

    change_status_activate = await UserService(
        uow=uow_factory(),
    ).activate_user(
        user_id=new_user.id,
    )
    stored_user = await UserService(
        uow=uow_factory(),
    ).get_user_by_id(
        user_id=new_user.id,
    )
    assert change_status_activate is True
    assert stored_user.is_active is True


@pytest.mark.usefixtures("truncate_tables")
@pytest.mark.anyio
async def test_update_user_profile(
    verify_user_service: UserService,
    fake_instance: Faker,
    fake_user_schema: UserCreate,
    fake_hasher: PasswordHasher,
    db_session: AsyncSession,
) -> None:
    """Test change user status."""
    new_user = User(
        email=fake_user_schema.email,
        plain_password=fake_user_schema.password,
        hasher=fake_hasher,
    )
    db_session.add(new_user)
    await db_session.commit()

    new_profile = ProfileUpdate(
        first_name=fake_instance.first_name(),
        last_name=fake_instance.last_name(),
        bio=fake_instance.name(),
    )
    updated_user_schema = await verify_user_service.update_user_profile(
        user_id=new_user.id,
        profile_data=new_profile,
    )

    assert isinstance(updated_user_schema, UserRead)
    assert isinstance(updated_user_schema.profile, ProfileRead)
    assert updated_user_schema.profile.id == new_user.profile.id
    assert updated_user_schema.profile.user_id == new_user.id
    assert updated_user_schema.profile.first_name == new_profile.first_name
    assert updated_user_schema.profile.last_name == new_profile.last_name
    assert updated_user_schema.profile.bio == new_profile.bio
