"""User-related service in 'app_auth'."""

import uuid

from project.app_auth.application.interfaces import AbstractUnitOfWork
from project.app_auth.application.schemas import ProfileUpdate, UserRead
from project.app_auth.domain.exceptions import UserNotFound
from project.app_auth.domain.models import User
from project.core.log_config import get_logger

logger = get_logger(__name__)


class UserService:
    """Application service for managing users."""

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        """Initialize the service object. Set UoW."""
        self.uow = uow

    async def _search_user(
        self,
        user_id: uuid.UUID | None = None,
        email: str | None = None,
    ) -> User:
        """Search the user in DB by his ID or email.

        Args:
            user_id (uuid.UUID | None, optional): User ID in DB.
                Defaults to None.
            email (str | None, optional): User email in DB. Defaults to None.

        Raises:
            UserNotFound: If searching user doesn't exist.

        Returns:
            User: User instance.
        """
        if user_id:
            unique_identifier: uuid.UUID | str = user_id
            user = await self.uow.users.get_by_id(user_id)
        elif email:
            unique_identifier = email
            user = await self.uow.users.get_by_email(email)

        if not user:
            logger.warning("User %s not found in DB", unique_identifier)
            raise UserNotFound(user_id, email)
        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID.

        Args:
            user_id (uuid.UUID): User ID in DB.

        Returns:
            UserRead | None: User data as pydantic schema.
        """
        async with self.uow:
            return await self.uow.users.get_by_id(user_id)

    async def get_by_id_detail(self, user_id: uuid.UUID) -> User | None:
        """Get the user by ID. Load related objects."""
        async with self.uow:
            return await self.uow.users.get_by_id_detail(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email.

        Args:
            email (str): User email in DB.

        Returns:
            UserRead | None: User data as pydantic schema.
        """
        async with self.uow:
            return await self.uow.users.get_by_email(email)

    async def get_all_users(self) -> list[UserRead]:
        """Get all users from DB.

        Returns:
            list[UserRead]: All users as pydantic schemas.
        """
        async with self.uow:
            users = await self.uow.users.list_all()
            return [UserRead.model_validate(user) for user in users]

    async def deactivate_user(
        self,
        user_id: uuid.UUID | None = None,
        email: str | None = None,
    ) -> bool:
        """Deactivate the user.

        Args:
            user_id (uuid.UUID | None, optional): User ID in DB.
                Defaults to None.
            email (str | None, optional): User email in DB. Defaults to None.

        Returns:
            bool: True if operation is successful.
        """
        async with self.uow:
            user: User = await self._search_user(user_id, email)
            user.deactivate()
            await self.uow.commit()
        return True

    async def activate_user(
        self,
        user_id: uuid.UUID | None = None,
        email: str | None = None,
    ) -> bool:
        """Activate the user.

        Args:
            user_id (uuid.UUID | None, optional): User ID in DB.
                Defaults to None.
            email (str | None, optional): User email in DB. Defaults to None.

        Returns:
            bool: True if operation is successful.
        """
        async with self.uow:
            user: User = await self._search_user(user_id, email)
            user.activate()
            await self.uow.commit()
        return True

    async def update_profile(
        self,
        user_id: uuid.UUID,
        data: ProfileUpdate,
    ) -> User:
        """Update user profile by user ID."""
        async with self.uow:
            user: User | None = await self.uow.users.get_by_id_detail(user_id)
            if not user:
                raise UserNotFound(user_id=user_id)

            update_data: dict = data.model_dump(exclude_unset=True)
            needs_update = False

            for field_name, field_value in update_data.items():
                if getattr(user.profile, field_name) != field_value:
                    setattr(user.profile, field_name, field_value)
                    needs_update = True

            if needs_update:
                await self.uow.commit()
                await self.uow.refresh(user, attribute_names=["profile"])

            return user
