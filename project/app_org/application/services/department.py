"""Department-related service in 'app_org'."""

import uuid

from project.app_org.application.interfaces import AbsUnitOfWork
from project.app_org.application.schemas import (
    DepartmentCreate,
    DepartmentUpdate,
)
from project.app_org.domain.exceptions import (
    CommandNotFound,
    DepartmentNotFound,
    RoleNotFound,
)
from project.app_org.domain.models import Department, Role
from project.core.log_config import get_logger

logger = get_logger(__name__)


class DepartmentService:
    """Application service for managing departments."""

    def __init__(self, uow: AbsUnitOfWork) -> None:
        """Initialize the service object. Set UoW."""
        self.uow = uow
        logger.debug("'%s' initialized", self.__class__.__name__)

    async def get_by_id(self, department_id: uuid.UUID) -> Department | None:
        """Get department by ID."""
        async with self.uow as uow:
            return await uow.departments.get_by_id(department_id)

    async def get_by_id_with_roles(
        self,
        department_id: uuid.UUID,
    ) -> Department | None:
        """Get department by ID. Use options to load related roles."""
        async with self.uow as uow:
            return await uow.departments.get_by_id_with_roles(department_id)

    async def get_all(self) -> list[Department]:
        """Get all departments from DB."""
        async with self.uow as uow:
            return await uow.departments.list_all()

    async def create(self, data: DepartmentCreate) -> Department:
        """Create a new department.

        Preliminary check that the command exists if 'command_id' in data.
        """
        async with self.uow as uow:
            if data.command_id:
                if not await uow.commands.get_by_id(data.command_id):
                    raise CommandNotFound(command_id=data.command_id)

            new_department = Department(**data.model_dump())
            await uow.departments.add(new_department)
            await uow.commit()
            await uow.refresh(new_department, attribute_names=["roles"])
            logger.debug(
                "Department instance '%s' refreshed after creating.",
                new_department.id,
            )
            return new_department

    async def update(
        self,
        department_id: uuid.UUID,
        data: DepartmentUpdate,
    ) -> Department:
        """Update the department info.

        Preliminary check that the command exists if 'command_id' in data.
        """
        async with self.uow as uow:
            upd_department = await uow.departments.get_by_id(department_id)
            if not upd_department:
                raise DepartmentNotFound(department_id=department_id)

            if data.command_id:
                if not await uow.commands.get_by_id(data.command_id):
                    raise CommandNotFound(command_id=data.command_id)

            update_data: dict = data.model_dump(exclude_unset=True)
            needs_update = False

            for field_name, field_value in update_data.items():
                if getattr(upd_department, field_name) != field_value:
                    setattr(upd_department, field_name, field_value)
                    needs_update = True

            if needs_update:
                await uow.commit()
                await uow.refresh(upd_department)
                logger.debug(
                    "Department instance '%s' refreshed after update.",
                    department_id,
                )

            return upd_department

    async def list_roles(
        self,
        department_id: uuid.UUID,
    ) -> list[Role]:
        """Get all roles inside the department."""
        async with self.uow as uow:
            department = await uow.departments.get_by_id(department_id)
            if not department:
                raise DepartmentNotFound(department_id=department_id)

            return department.roles

    async def add_role(
        self,
        department_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> Department:
        """Add role to the department."""
        async with self.uow as uow:
            department = await uow.departments.get_by_id_with_roles(
                department_id=department_id,
            )
            if not department:
                raise DepartmentNotFound(department_id=department_id)

            role: Role | None = await uow.roles.get_by_id(role_id)
            if not role:
                raise RoleNotFound(role_id)

            if role not in department.roles:
                department.roles.append(role)
                await uow.commit()
                logger.debug(
                    "Role '%s' added to department '%s'",
                    role_id,
                    department_id,
                )

            logger.debug(
                "Department '%s' already contains the role '%s'",
                department_id,
                role_id,
            )

            return department

    async def exclude_role(
        self,
        department_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> Department:
        """Exclude department from the command."""
        async with self.uow as uow:
            department = await uow.departments.get_by_id_with_roles(
                department_id=department_id,
            )
            if not department:
                raise DepartmentNotFound(department_id=department_id)

            role: Role | None = await uow.roles.get_by_id(role_id)
            if not role:
                raise RoleNotFound(role_id)

            if role in department.roles:
                department.roles.remove(role)
                await uow.commit()
                logger.debug(
                    "Role '%s' excluded from department '%s'",
                    role_id,
                    department_id,
                )

            logger.debug(
                "Department '%s' isn't contain the role '%s'",
                department_id,
                role_id,
            )

            return department
