"""Command-related service in 'app_org'."""

import uuid

from project.app_org.application.interfaces import AbsUnitOfWork
from project.app_org.application.schemas import (
    CommandCreate,
    CommandUpdate,
)
from project.app_org.domain.exceptions import (
    CommandNameExistsError,
    CommandNotFound,
    DepartmentNotFound,
)
from project.app_org.domain.models import Command, Department
from project.core.log_config import get_logger

logger = get_logger(__name__)


class CommandService:
    """Application service for managing commands."""

    def __init__(self, uow: AbsUnitOfWork) -> None:
        """Initialize the service object. Set UoW."""
        self.uow = uow
        logger.debug("'%s' initialized", self.__class__.__name__)

    async def get_by_id(self, command_id: uuid.UUID) -> Command | None:
        """Get command by ID."""
        async with self.uow as uow:
            return await uow.commands.get_by_id(command_id)

    async def get_by_name(self, name: str) -> Command | None:
        """Get command by name."""
        async with self.uow as uow:
            return await uow.commands.get_by_name(name)

    async def get_all(self) -> list[Command]:
        """Get all commands from DB."""
        async with self.uow as uow:
            return await uow.commands.list_all()

    async def create(self, data: CommandCreate) -> Command:
        """Create a new command.

        Preliminary check that the name of the new command is unique.
        """
        async with self.uow as uow:
            if await uow.commands.get_by_name(data.name):
                raise CommandNameExistsError(name=data.name)

            new_command = Command(**data.model_dump())
            await uow.commands.add(new_command)
            await uow.commit()

            return new_command

    async def update(
        self,
        command_id: uuid.UUID,
        data: CommandUpdate,
    ) -> Command:
        """Update the command info.

        Preliminary check that the name of the new command is unique.
        """
        async with self.uow as uow:
            upd_command = await uow.commands.get_by_id(command_id)
            if not upd_command:
                raise CommandNotFound(command_id=command_id)

            if data.name:
                command_by_name = await uow.commands.get_by_name(data.name)
                if command_by_name and command_by_name.id != upd_command.id:
                    # найдена существующая команда с таким же именем
                    raise CommandNameExistsError(name=data.name)

            update_data: dict = data.model_dump(exclude_unset=True)
            for field_name, field_value in update_data.items():
                setattr(upd_command, field_name, field_value)

            await uow.commit()

            return upd_command

    async def list_departments(
        self,
        command_id: uuid.UUID,
    ) -> list[Department]:
        """Get all department inside the command."""
        async with self.uow as uow:
            command = await uow.commands.get_by_id(command_id)
            if not command:
                raise CommandNotFound(command_id=command_id)

            return command.departments

    async def add_department(
        self,
        command_id: uuid.UUID,
        department_id: uuid.UUID,
    ) -> Command:
        """Add department to the command."""
        async with self.uow as uow:
            command = await uow.commands.get_by_id(command_id)
            if not command:
                raise CommandNotFound(command_id=command_id)

            department: Department | None = await uow.departments.get_by_id(
                department_id=department_id,
            )
            if not department:
                raise DepartmentNotFound(department_id)

            if department not in command.departments:
                command.departments.append(department)
                await uow.commit()
                logger.debug(
                    "Department '%s' added to command '%s'",
                    department_id,
                    command_id,
                )

            logger.debug(
                "Command '%s' already contains the department '%s'",
                command_id,
                department_id,
            )

            return command

    async def exclude_department(
        self,
        command_id: uuid.UUID,
        department_id: uuid.UUID,
    ) -> Command:
        """Exclude department from the command."""
        async with self.uow as uow:
            command = await uow.commands.get_by_id(command_id)
            if not command:
                raise CommandNotFound(command_id=command_id)

            department: Department | None = await uow.departments.get_by_id(
                department_id=department_id,
            )
            if not department:
                raise DepartmentNotFound(department_id)

            if department in command.departments:
                command.departments.remove(department)
                await uow.commit()
                logger.debug(
                    "Department '%s' excluded from command '%s'",
                    department_id,
                    command_id,
                )

            logger.debug(
                "Command '%s' isn't contain the department '%s'",
                command_id,
                department_id,
            )

            return command
