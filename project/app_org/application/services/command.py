"""Command-related service in 'app_org'."""

import uuid

from project.app_org.application.schemas import (
    CommandCreate,
    CommandUpdate,
)
from project.app_org.domain.exceptions import (
    CommandNameExistsError,
    CommandNotEmpty,
    CommandNotFound,
)
from project.app_org.domain.models import Command
from project.app_org.infrastructure.unit_of_work import SAOrgUnitOfWork
from project.core.db.utils import check_active_relationships
from project.core.log_config import get_logger

logger = get_logger(__name__)


class CommandService:
    """Application service for managing commands."""

    def __init__(self, uow: SAOrgUnitOfWork) -> None:
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
            await uow.refresh(new_command)
            logger.debug(
                "Command instance '%s' refreshed after creating.",
                new_command.id,
            )
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
                logger.warning("Command with id '%s' not found", command_id)
                raise CommandNotFound(command_id=command_id)

            if data.name:
                command_by_name = await uow.commands.get_by_name(data.name)
                if command_by_name and command_by_name.id != upd_command.id:
                    # найдена существующая команда с таким же именем
                    raise CommandNameExistsError(name=data.name)

            update_data: dict = data.model_dump(exclude_unset=True)

            for field_name, field_value in update_data.items():
                setattr(upd_command, field_name, field_value)

            if update_data:
                await uow.commit()
                await uow.refresh(upd_command)
                logger.debug(
                    "Command instance '%s' refreshed after update.", command_id
                )

            return upd_command

    async def deactivate(self, command_id: uuid.UUID) -> bool:
        """Deactivate the command."""
        async with self.uow as uow:
            command: Command | None = await uow.commands.get_by_id_detail(
                command_id
            )
            if not command:
                raise CommandNotFound(command_id)

            active_relationships = check_active_relationships(command)
            if active_relationships:
                raise CommandNotEmpty(
                    command_name=command.name,
                    rel_names=active_relationships,
                )

            if command.is_active:
                command.is_active = False
                await uow.commit()
                await uow.refresh(command)
        return True

    async def activate(self, command_id: uuid.UUID) -> bool:
        """Activate the command."""
        async with self.uow as uow:
            command: Command | None = await uow.commands.get_by_id(command_id)
            if not command:
                raise CommandNotFound(command_id)

            command.is_active = True
            await uow.commit()
        return True
