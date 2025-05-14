"""Department and Command related service in 'app_org'."""

import uuid

from project.app_org.domain.exceptions import (
    CommandNotFound,
    DepartmentNotFound,
)
from project.app_org.domain.models import Command, Department
from project.app_org.infrastructure.unit_of_work import SAOrgUnitOfWork
from project.core.log_config import get_logger

logger = get_logger(__name__)


class DepartmentInCommandService:
    """Implementation of departmental operations within the command."""

    def __init__(self, uow: SAOrgUnitOfWork) -> None:
        """Initialize the service object. Set UoW."""
        self.uow = uow
        logger.debug("'%s' initialized", self.__class__.__name__)

    async def get_by_id_with_departments(
        self,
        command_id: uuid.UUID,
    ) -> Command | None:
        """Get command by ID. Use options to load related departments."""
        async with self.uow as uow:
            return await uow.commands.get_by_id_with_departments(command_id)

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
            command = await uow.commands.get_by_id_with_departments(command_id)
            if not command:
                raise CommandNotFound(command_id=command_id)

            department: Department | None = await uow.departments.get_by_id(
                department_id=department_id,
            )
            if not department:
                raise DepartmentNotFound(department_id)

            if department.id not in [dep.id for dep in command.departments]:
                command.departments.append(department)
                await uow.commit()
                logger.debug(
                    "Department '%s' added to command '%s'",
                    department_id,
                    command_id,
                )
            else:
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
            command = await uow.commands.get_by_id_with_departments(command_id)
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
