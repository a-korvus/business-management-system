"""Role-related service in 'app_org'."""

import uuid

from project.app_org.application.schemas import RoleCreate, RoleUpdate
from project.app_org.domain.exceptions import (
    DepartmentNotFound,
    RoleNotEmpty,
    RoleNotFound,
)
from project.app_org.domain.models import Role
from project.app_org.infrastructure.unit_of_work import SAOrgUnitOfWork
from project.core.db.utils import check_active_relationships
from project.core.log_config import get_logger

logger = get_logger(__name__)


class RoleService:
    """Application service for managing roles."""

    def __init__(self, uow: SAOrgUnitOfWork) -> None:
        """Initialize the service object. Set UoW."""
        self.uow = uow
        logger.debug("'%s' initialized", self.__class__.__name__)

    async def get_by_id(self, role_id: uuid.UUID) -> Role | None:
        """Get role by ID."""
        async with self.uow as uow:
            return await uow.roles.get_by_id(role_id)

    async def get_by_id_with_users(
        self,
        role_id: uuid.UUID,
    ) -> Role | None:
        """Get role by ID. Use options to load related users."""
        async with self.uow as uow:
            return await uow.roles.get_by_id_with_users(role_id)

    async def get_all(self) -> list[Role]:
        """Get all roles from DB."""
        async with self.uow as uow:
            return await uow.roles.list_all()

    async def create(self, data: RoleCreate) -> Role:
        """Create a new role.

        Preliminary check that the department exists if 'department_id'
        in creating data.
        Check that the RoleType Enum contains the new role name occurs at the
        schema level in a FastAPI request handler.
        """
        async with self.uow as uow:
            if data.department_id:
                if not await uow.departments.get_by_id(data.department_id):
                    raise DepartmentNotFound(department_id=data.department_id)

            new_role = Role(**data.model_dump(exclude_unset=True))
            await uow.roles.add(new_role)
            await uow.commit()
            await uow.refresh(
                new_role,
                attribute_names=["department", "users"],
            )
            logger.debug(
                "Role instance '%s' refreshed after creating.",
                new_role.id,
            )

            return new_role

    async def update(
        self,
        role_id: uuid.UUID,
        data: RoleUpdate,
    ) -> Role:
        """Update the role info.

        Preliminary check that the department exists if 'department_id'
        in updating data.
        """
        async with self.uow as uow:
            upd_role = await uow.roles.get_by_id(role_id)
            if not upd_role:
                logger.warning("Role with id '%s' not found", role_id)
                raise RoleNotFound(role_id=role_id)

            if data.department_id:
                if not await uow.departments.get_by_id(data.department_id):
                    logger.warning(
                        "Department with id '%s' not found", data.department_id
                    )
                    raise DepartmentNotFound(department_id=data.department_id)

            update_data: dict = data.model_dump(exclude_unset=True)

            for field_name, field_value in update_data.items():
                setattr(upd_role, field_name, field_value)

            if update_data:
                await uow.commit()
                await uow.refresh(upd_role)
                logger.debug(
                    "Role instance '%s' refreshed after update.", role_id
                )

            return upd_role

    async def deactivate(self, role_id: uuid.UUID) -> bool:
        """Deactivate the role."""
        async with self.uow as uow:
            role: Role | None = await uow.roles.get_by_id_detail(role_id)
            if not role:
                raise RoleNotFound(role_id)

            active_relationships = check_active_relationships(role)
            if active_relationships:
                raise RoleNotEmpty(
                    role_name=role.name.value,
                    rel_names=active_relationships,
                )

            if role.is_active:
                role.is_active = False
                await uow.commit()
                await uow.refresh(role)
        return True

    async def activate(self, role_id: uuid.UUID) -> bool:
        """Activate the role."""
        async with self.uow as uow:
            role: Role | None = await uow.roles.get_by_id(
                role_id=role_id,
            )
            if not role:
                raise RoleNotFound(role_id)

            role.is_active = True
            await uow.commit()
        return True
