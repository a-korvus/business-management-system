"""Project service orchestrator. Use it to manage different repositories."""

import uuid

from project.app_auth.application.schemas import UserCreate
from project.app_auth.domain.exceptions import EmailAlreadyExists, UserNotFound
from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_auth.infrastructure.unit_of_work import (
    SAAuthUnitOfWork as app_auth_uow,
)
from project.app_org.domain.exceptions import CommandNotFound, RoleNotFound
from project.app_org.domain.models import Role
from project.app_org.infrastructure.unit_of_work import (
    SAOrgUnitOfWork as app_org_uow,
)
from project.core.db.setup import AsyncSessionFactory


class CoreService:
    """Project core service."""

    def __init__(self) -> None:
        """Set all needed UoW."""
        self.uow_auth = app_auth_uow
        self.uow_org = app_org_uow

    async def create_user(self, schema: UserCreate) -> User:
        """Create user with simple password."""
        async with AsyncSessionFactory() as session:
            async with (
                self.uow_auth(session=session) as uow_auth,
                self.uow_org(session=session) as uow_org,
            ):
                existing_user = await uow_auth.users.get_by_email(schema.email)
                if existing_user:
                    raise EmailAlreadyExists(schema.email)

                if schema.command_id:
                    if not await uow_org.commands.get_by_id(schema.command_id):
                        raise CommandNotFound(command_id=schema.command_id)

                if schema.role_id:
                    if not await uow_org.roles.get_by_id(schema.role_id):
                        raise RoleNotFound(schema.role_id)

                creating_data: dict = schema.model_dump(exclude_unset=True)
                creating_data["plain_password"] = creating_data.pop("password")
                new_user = User(
                    hasher=get_password_hasher(),
                    **creating_data,
                )
                await uow_auth.users.add(new_user)
                await uow_auth.commit()
                await uow_auth.refresh(new_user, attribute_names=["profile"])

                return new_user

    async def assign_user_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> User:
        """Assign a role to a user."""
        async with AsyncSessionFactory() as session:
            async with (
                self.uow_auth(session=session) as uow_auth,
                self.uow_org(session=session) as uow_org,
            ):
                user: User | None = await uow_auth.users.get_by_id(user_id)
                if not user:
                    raise UserNotFound(user_id=user_id)

                role: Role | None = await uow_org.roles.get_by_id(role_id)
                if not role:
                    raise RoleNotFound(role_id=role_id)

                if user.role_id != role_id:
                    user.role_id = role_id
                    await uow_auth.commit()
                    await uow_auth.refresh(user)

                return user


def get_core_service() -> CoreService:
    """Get core service instance to use it in the project."""
    return CoreService()
