"""Test RoleService from 'app_org' app."""

import random
from datetime import datetime
from typing import Callable

import pytest
from faker import Faker
from sqlalchemy.exc import MissingGreenlet

from project.app_org.application.interfaces import AbsUnitOfWork
from project.app_org.application.schemas import RoleCreate, RoleUpdate
from project.app_org.application.services.role import RoleService
from project.app_org.domain.models import Role
from project.core.log_config import get_logger

logger = get_logger(__name__)

pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]


async def test_create(
    verify_role_service: RoleService,
    fake_role_schema: RoleCreate,
) -> None:
    """Test creating a role."""
    role = await verify_role_service.create(fake_role_schema)

    assert isinstance(role, Role)
    assert role.id is not None
    assert isinstance(role.created_at, datetime)
    assert isinstance(role.updated_at, datetime)
    assert role.department is None
    assert isinstance(role.users, list)
    assert len(role.users) == 0


async def test_get_by_id(
    verify_role_service: RoleService,
    fake_role_schema: RoleCreate,
    uow_sess_factory: Callable[[], AbsUnitOfWork],
) -> None:
    """Test retrieving the existing role by its ID."""
    alter_role_service = RoleService(uow_sess_factory())
    new_role = await alter_role_service.create(fake_role_schema)

    assert isinstance(new_role, Role)

    role = await verify_role_service.get_by_id(new_role.id)

    assert isinstance(role, Role)
    assert new_role.id == role.id
    with pytest.raises(MissingGreenlet):
        role.users


async def test_get_by_id_with_users(
    verify_role_service: RoleService,
    fake_role_schema: RoleCreate,
    uow_sess_factory: Callable[[], AbsUnitOfWork],
) -> None:
    """Test retrieving the existing role by its ID. With related users."""
    alter_role_service = RoleService(uow_sess_factory())
    new_role = await alter_role_service.create(fake_role_schema)

    assert isinstance(new_role, Role)

    role = await verify_role_service.get_by_id_with_users(new_role.id)

    assert isinstance(role, Role)
    assert new_role.id == role.id
    assert new_role.users == role.users


async def test_get_all(
    verify_role_service: RoleService,
    fake_role_schema: RoleCreate,
) -> None:
    """Test retrieving all existing roles."""
    roles_count = 0
    for _ in range(random.randint(10, 30)):
        await verify_role_service.create(data=fake_role_schema)
        roles_count += 1

    roles = await verify_role_service.get_all()

    assert isinstance(roles, list)
    assert roles_count == len(roles)


async def test_update(
    verify_role_service: RoleService,
    fake_role_schema: RoleCreate,
    uow_sess_factory: Callable[[], AbsUnitOfWork],
    fake_instance: Faker,
) -> None:
    """Test updating the existing role."""
    alter_role_service = RoleService(uow=uow_sess_factory())
    new_role = await alter_role_service.create(
        data=fake_role_schema,
    )

    assert isinstance(new_role, Role)

    updating_data = RoleUpdate(
        description=fake_instance.text(max_nb_chars=500),
    )

    updated_role = await verify_role_service.update(
        role_id=new_role.id,
        data=updating_data,
    )

    assert isinstance(updated_role, Role)
    assert new_role.id == updated_role.id
    assert new_role.description != updated_role.description
    assert updating_data.description == updated_role.description
    assert updated_role.updated_at > new_role.updated_at
