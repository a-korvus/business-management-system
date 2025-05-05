"""Test CommandService from 'app_org' app."""

import random
from datetime import datetime
from typing import Callable

import pytest
from faker import Faker

from project.app_org.application.interfaces import AbsUnitOfWork
from project.app_org.application.schemas import (
    CommandCreate,
    CommandUpdate,
    DepartmentCreate,
)
from project.app_org.application.services.command import CommandService
from project.app_org.application.services.department import DepartmentService
from project.app_org.domain.exceptions import CommandNameExistsError
from project.app_org.domain.models import Command, Department
from project.core.log_config import get_logger

logger = get_logger(__name__)

pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]


async def test_create(
    verify_command_service: CommandService,
    fake_command_schema: CommandCreate,
) -> None:
    """Test creating a command."""
    new_command = await verify_command_service.create(data=fake_command_schema)

    assert isinstance(new_command, Command)
    assert new_command.id is not None
    assert isinstance(new_command.created_at, datetime)
    assert isinstance(new_command.updated_at, datetime)
    assert isinstance(new_command.departments, list)
    assert len(new_command.departments) == 0

    with pytest.raises(CommandNameExistsError):
        await verify_command_service.create(data=fake_command_schema)


async def test_get_by_id(
    verify_command_service: CommandService,
    fake_command_schema: CommandCreate,
) -> None:
    """Test retrieving the existing command by its ID."""
    new_command = await verify_command_service.create(data=fake_command_schema)

    assert isinstance(new_command, Command)

    command = await verify_command_service.get_by_id(command_id=new_command.id)

    assert isinstance(command, Command)
    assert new_command.id == command.id
    assert new_command.departments == command.departments


async def test_get_by_id_with_departments(
    verify_command_service: CommandService,
    fake_command_schema: CommandCreate,
) -> None:
    """Test retrieving the existing command by its ID.

    With related departments.
    """
    new_command = await verify_command_service.create(data=fake_command_schema)

    assert isinstance(new_command, Command)

    command = await verify_command_service.get_by_id_with_departments(
        command_id=new_command.id
    )

    assert isinstance(command, Command)
    assert new_command.id == command.id
    assert new_command.departments == command.departments


async def test_get_by_name(
    verify_command_service: CommandService,
    fake_command_schema: CommandCreate,
) -> None:
    """Test retrieving the existing command by its unique name."""
    new_command = await verify_command_service.create(data=fake_command_schema)

    assert isinstance(new_command, Command)

    command = await verify_command_service.get_by_name(name=new_command.name)

    assert isinstance(command, Command)
    assert new_command.id == command.id
    assert new_command.departments == command.departments


async def test_get_all(
    verify_command_service: CommandService,
    fake_instance: Faker,
) -> None:
    """Test retrieving all existing commands."""
    command_count = 0
    for _ in range(random.randint(10, 30)):
        unique_schema = CommandCreate(name=fake_instance.unique.company())
        await verify_command_service.create(data=unique_schema)
        command_count += 1

    commands = await verify_command_service.get_all()

    assert isinstance(commands, list)
    assert command_count == len(commands)


async def test_update(
    verify_command_service: CommandService,
    fake_command_schema: CommandCreate,
    uow_sess_factory: Callable[[], AbsUnitOfWork],
    fake_instance: Faker,
) -> None:
    """Test updating the existing command."""
    alter_command_service = CommandService(uow=uow_sess_factory())
    new_command = await alter_command_service.create(data=fake_command_schema)

    assert isinstance(new_command, Command)

    updating_data = CommandUpdate(
        description=fake_instance.text(max_nb_chars=500),
    )
    updated_command = await verify_command_service.update(
        command_id=new_command.id,
        data=updating_data,
    )

    assert isinstance(updated_command, Command)
    assert new_command.id == updated_command.id
    assert new_command.description != updated_command.description
    assert updating_data.description == updated_command.description
    assert updated_command.updated_at > new_command.updated_at


async def test_add_exclude_department(
    verify_command_service: CommandService,
    verify_department_service: DepartmentService,
    fake_command_schema: CommandCreate,
    fake_department_schema: DepartmentCreate,
    uow_sess_factory: Callable[[], AbsUnitOfWork],
) -> None:
    """Test adding a department to a command and exclusion from."""
    # создать команду
    command_service = CommandService(uow=uow_sess_factory())
    command = await command_service.create(data=fake_command_schema)

    assert isinstance(command, Command)
    assert len(command.departments) == 0

    # создать департамент
    department = await verify_department_service.create(
        data=fake_department_schema,
    )

    assert isinstance(department, Department)
    assert department.id is not None
    assert department.command_id is None

    # добавить департамент в команду
    await verify_command_service.add_department(
        command_id=command.id,
        department_id=department.id,
    )

    # проверить, что он есть, выгрузив команду по ID
    adding_command_service = CommandService(uow=uow_sess_factory())
    updated_command = await adding_command_service.get_by_id_with_departments(
        command_id=command.id,
    )

    assert isinstance(updated_command, Command)
    assert department.id in [dep.id for dep in updated_command.departments]

    # удалить департамент из команды
    excluding_command_service = CommandService(uow=uow_sess_factory())
    await excluding_command_service.exclude_department(
        command_id=command.id,
        department_id=department.id,
    )

    # проверить, что его больше нет в команде
    final_command_service = CommandService(uow=uow_sess_factory())
    final_command = await final_command_service.get_by_id_with_departments(
        command_id=command.id,
    )

    assert isinstance(final_command, Command)
    assert department.id not in [dep.id for dep in final_command.departments]


async def test_list_departments(
    verify_command_service: CommandService,
    verify_department_service: DepartmentService,
    fake_command_schema: CommandCreate,
    fake_department_schema: DepartmentCreate,
    uow_sess_factory: Callable[[], AbsUnitOfWork],
) -> None:
    """Test retrieving all command-related departments."""
    command = await verify_command_service.create(fake_command_schema)

    department_count = 0
    for _ in range(random.randint(10, 20)):
        department = await verify_department_service.create(
            data=fake_department_schema,
        )
        await verify_command_service.add_department(
            command_id=command.id,
            department_id=department.id,
        )
        department_count += 1

    alter_command_service = CommandService(uow=uow_sess_factory())
    upgraded_command = await alter_command_service.get_by_id_with_departments(
        command_id=command.id,
    )

    assert isinstance(upgraded_command, Command)
    assert len(upgraded_command.departments) == department_count
