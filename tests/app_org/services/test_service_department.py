"""Test DepartmentService from 'app_org' app."""

import random
from datetime import datetime
from typing import Callable

import pytest
from faker import Faker

from project.app_org.application.schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    RoleCreate,
)
from project.app_org.application.services.department import DepartmentService
from project.app_org.application.services.role import RoleService
from project.app_org.domain.models import Department, Role
from project.app_org.infrastructure.unit_of_work import SAOrgUnitOfWork
from project.core.log_config import get_logger

logger = get_logger(__name__)

pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]


async def test_create(
    verify_department_service: DepartmentService,
    fake_department_schema: DepartmentCreate,
) -> None:
    """Test creating a department."""
    department = await verify_department_service.create(fake_department_schema)

    assert isinstance(department, Department)
    assert department.id is not None
    assert department.is_active is True
    assert isinstance(department.created_at, datetime)
    assert isinstance(department.updated_at, datetime)
    assert isinstance(department.roles, list)
    assert len(department.roles) == 0


async def test_get_by_id(
    verify_department_service: DepartmentService,
    fake_department_schema: DepartmentCreate,
) -> None:
    """Test retrieving the existing department by its ID."""
    new_department = await verify_department_service.create(
        data=fake_department_schema,
    )

    assert isinstance(new_department, Department)

    department = await verify_department_service.get_by_id(
        department_id=new_department.id,
    )

    assert isinstance(department, Department)
    assert new_department.id == department.id
    assert new_department.roles == department.roles


async def test_get_by_id_with_roles(
    verify_department_service: DepartmentService,
    fake_department_schema: DepartmentCreate,
) -> None:
    """Test retrieving the existing department by its ID.

    With related roles.
    """
    new_department = await verify_department_service.create(
        data=fake_department_schema,
    )

    assert isinstance(new_department, Department)

    department = await verify_department_service.get_by_id_with_roles(
        department_id=new_department.id
    )

    assert isinstance(department, Department)
    assert new_department.id == department.id
    assert new_department.roles == department.roles


async def test_get_all(
    verify_department_service: DepartmentService,
    fake_department_schema: DepartmentCreate,
) -> None:
    """Test retrieving all existing departments."""
    departments_count = 0
    for _ in range(random.randint(10, 30)):
        await verify_department_service.create(data=fake_department_schema)
        departments_count += 1

    departments = await verify_department_service.get_all()

    assert isinstance(departments, list)
    assert departments_count == len(departments)


async def test_update(
    verify_department_service: DepartmentService,
    fake_department_schema: DepartmentCreate,
    uow_sess_factory: Callable[[], SAOrgUnitOfWork],
    fake_instance: Faker,
) -> None:
    """Test updating the existing department."""
    alter_department_service = DepartmentService(uow=uow_sess_factory())
    new_department = await alter_department_service.create(
        data=fake_department_schema,
    )

    assert isinstance(new_department, Department)

    updating_data = DepartmentUpdate(
        description=fake_instance.text(max_nb_chars=500),
        name=fake_instance.company(),
    )
    updated_department = await verify_department_service.update(
        department_id=new_department.id,
        data=updating_data,
    )

    assert isinstance(updated_department, Department)
    assert new_department.id == updated_department.id
    assert new_department.description != updated_department.description
    assert new_department.name != updated_department.name
    assert updating_data.description == updated_department.description
    assert updating_data.name == updated_department.name
    assert updated_department.updated_at > new_department.updated_at


async def test_add_exclude_role(
    verify_department_service: DepartmentService,
    verify_role_service: RoleService,
    fake_department_schema: DepartmentCreate,
    fake_role_schema: RoleCreate,
    uow_sess_factory: Callable[[], SAOrgUnitOfWork],
) -> None:
    """Test adding a role to a department and exclusion from."""
    # создать департамент
    dep_service = DepartmentService(uow=uow_sess_factory())
    department = await dep_service.create(data=fake_department_schema)

    assert isinstance(department, Department)
    assert len(department.roles) == 0

    # создать роль
    role = await verify_role_service.create(
        data=fake_role_schema,
    )

    assert isinstance(role, Role)
    assert role.id is not None
    assert role.department_id is None

    # добавить роль в департамент
    await verify_department_service.add_role(
        department_id=department.id,
        role_id=role.id,
    )

    # проверить, что она есть, выгрузив департамент по ID
    adding_dep_service = DepartmentService(uow=uow_sess_factory())
    updated_dep = await adding_dep_service.get_by_id_with_roles(
        department_id=department.id,
    )

    assert isinstance(updated_dep, Department)
    assert role.id in [role.id for role in updated_dep.roles]

    # удалить роль из департамента
    excluding_dep_service = DepartmentService(uow=uow_sess_factory())
    await excluding_dep_service.exclude_role(
        department_id=department.id,
        role_id=role.id,
    )

    # проверить, что ее больше нет в департаменте
    final_dep_service = DepartmentService(uow=uow_sess_factory())
    final_dep = await final_dep_service.get_by_id_with_roles(
        department_id=department.id,
    )

    assert isinstance(final_dep, Department)
    assert role.id not in [role.id for role in final_dep.roles]


async def test_list_roles(
    verify_department_service: DepartmentService,
    verify_role_service: RoleService,
    fake_department_schema: DepartmentCreate,
    fake_role_schema: RoleCreate,
    uow_sess_factory: Callable[[], SAOrgUnitOfWork],
) -> None:
    """Test retrieving all department-related roles."""
    department = await verify_department_service.create(fake_department_schema)

    role_count = 0
    for _ in range(random.randint(10, 20)):
        role = await verify_role_service.create(
            data=fake_role_schema,
        )
        await verify_department_service.add_role(
            department_id=department.id,
            role_id=role.id,
        )
        role_count += 1

    alter_dep_service = DepartmentService(uow=uow_sess_factory())
    upgraded_dep = await alter_dep_service.get_by_id_with_roles(
        department_id=department.id,
    )

    assert isinstance(upgraded_dep, Department)
    assert len(upgraded_dep.roles) == role_count


async def test_deactivate_activate(
    verify_department_service: DepartmentService,
    fake_department_schema: DepartmentCreate,
    uow_sess_factory: Callable[[], SAOrgUnitOfWork],
) -> None:
    """Test deactivating the existing department and then activating it."""
    alter_department_service = DepartmentService(uow=uow_sess_factory())
    new_department = await alter_department_service.create(
        data=fake_department_schema,
    )

    assert isinstance(new_department, Department)
    assert new_department.is_active is True

    await verify_department_service.deactivate(new_department.id)

    deact_department = await alter_department_service.get_by_id(
        department_id=new_department.id,
    )
    assert isinstance(deact_department, Department)
    assert deact_department.is_active is False

    await verify_department_service.activate(new_department.id)

    act_department = await alter_department_service.get_by_id(
        department_id=new_department.id,
    )
    assert isinstance(act_department, Department)
    assert act_department.is_active is True
