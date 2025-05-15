"""Tests core service."""

import pytest

from project.app_auth.application.schemas import UserCreate
from project.app_auth.domain.models import User
from project.app_org.application.schemas import RoleCreate
from project.app_org.application.services.role import RoleService
from project.app_org.infrastructure.unit_of_work import SAOrgUnitOfWork
from project.core.db.setup import AsyncSessionFactory
from project.core.service import get_core_service


@pytest.mark.usefixtures("truncate_tables")
@pytest.mark.anyio
async def test_create_user(
    fake_user_schema: UserCreate,
) -> None:
    """Test creating user."""
    core_service = get_core_service()

    new_user: User = await core_service.create_user(fake_user_schema)

    assert new_user.id is not None
    assert new_user.email == fake_user_schema.email
    assert new_user.hashed_password is not None
    assert new_user.command_id is None
    assert new_user.role_id is None


@pytest.mark.usefixtures("truncate_tables")
@pytest.mark.anyio
async def test_assign_user_role(fake_user_schema: UserCreate) -> None:
    """Test successful user role assigning."""
    org_uow = SAOrgUnitOfWork(session_factory=AsyncSessionFactory)
    role_service = RoleService(uow=org_uow)

    core_service = get_core_service()

    new_user: User = await core_service.create_user(fake_user_schema)

    assert new_user.id is not None
    assert new_user.role_id is None

    new_role = await role_service.create(RoleCreate())

    assert new_role.id is not None

    assignment_user = await core_service.assign_user_role(
        user_id=new_user.id,
        role_id=new_role.id,
    )

    assert assignment_user.id == new_user.id
    assert assignment_user.role_id == new_role.id
