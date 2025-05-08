"""Test UserService from 'app_auth' app."""

import random
from typing import Callable

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.application.interfaces import PasswordHasher
from project.app_auth.application.schemas import (
    LoginSchema,
    ProfileUpdate,
    UserCreate,
    UserRead,
)
from project.app_auth.application.services.auth import AuthService
from project.app_auth.application.services.users import UserService
from project.app_auth.domain.models import Profile, User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_org.application.schemas import RoleCreate
from project.app_org.application.services.role import RoleService
from project.app_org.domain.models import Role
from project.app_org.infrastructure.unit_of_work import SAOrgUnitOfWork
from project.core.db.setup import AsyncSessionFactory
from project.core.interfaces import AbsUnitOfWork

pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]


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
        User(
            email=schema.email,
            plain_password=schema.password,
            hasher=fake_hasher,
        )
        for schema in schemas
    ]
    db_session.add_all(users)
    await db_session.commit()

    stored_users = await verify_user_service.get_all_users()

    assert isinstance(stored_users, list)
    assert len(users) == len(stored_users)
    for stored_user in stored_users:
        assert isinstance(stored_user, UserRead)


async def test_deactivate_activate_user(
    verify_user_service: UserService,
    uow_factory: Callable[[], AbsUnitOfWork],
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


async def test_update_profile(
    verify_user_service: UserService,
    fake_user_schema: UserCreate,
    fake_instance: Faker,
    fake_hasher: PasswordHasher,
    db_session: AsyncSession,
) -> None:
    """Test updating the user profile."""
    new_user = User(
        email=fake_user_schema.email,
        plain_password=fake_user_schema.password,
        hasher=fake_hasher,
    )
    db_session.add(new_user)
    await db_session.commit()

    assert isinstance(new_user, User)
    assert new_user.id is not None

    updated_data = ProfileUpdate(
        first_name=fake_instance.first_name(),
        bio=fake_instance.text(max_nb_chars=255),
    )

    user_detail = await verify_user_service.update_profile(
        user_id=new_user.id,
        data=updated_data,
    )

    assert isinstance(user_detail, User)
    assert user_detail.id == new_user.id
    assert isinstance(user_detail.profile, Profile)
    assert user_detail.profile.first_name == updated_data.first_name
    assert user_detail.profile.bio == updated_data.bio
    assert user_detail.profile.last_name is None


async def test_restore_user(
    verify_user_service: UserService,
    fake_user_schema: UserCreate,
    db_session: AsyncSession,
) -> None:
    """Test restoring deactivated user. Using a real password hasher."""
    new_user = User(
        email=fake_user_schema.email,
        plain_password=fake_user_schema.password,
        hasher=get_password_hasher(),
    )
    db_session.add(new_user)
    await db_session.commit()

    assert isinstance(new_user, User)
    assert new_user.id is not None
    assert new_user.is_active

    new_user.deactivate()

    await db_session.commit()

    assert not new_user.is_active

    credentials = LoginSchema(
        username=fake_user_schema.email,
        password=fake_user_schema.password,
    )
    restored_user = await verify_user_service.restore_user(credentials)

    assert isinstance(restored_user, User)
    assert restored_user.id == new_user.id
    assert restored_user.is_active


async def test_revoke_role(
    verify_user_service: UserService,
    fake_user_schema: UserCreate,
    fake_hasher: PasswordHasher,
    db_session: AsyncSession,
) -> None:
    """Test revoking user role."""
    new_user = User(
        email=fake_user_schema.email,
        plain_password=fake_user_schema.password,
        hasher=fake_hasher,
    )
    db_session.add(new_user)
    await db_session.commit()

    assert isinstance(new_user, User)
    assert new_user.id is not None
    assert new_user.role_id is None

    role_service = RoleService(
        uow=SAOrgUnitOfWork(session_factory=AsyncSessionFactory),
    )

    new_role = await role_service.create(RoleCreate())

    assert isinstance(new_role, Role)
    assert new_role.id is not None

    new_user.role_id = new_role.id
    await db_session.commit()

    assert new_user.role_id == new_role.id

    demoted_user = await verify_user_service.revoke_role(user_id=new_user.id)

    assert isinstance(demoted_user, User)
    assert demoted_user.id == new_user.id
    assert demoted_user.role_id is None
