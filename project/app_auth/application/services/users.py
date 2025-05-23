"""User-related service in 'app_auth'."""

import uuid

from project.app_auth.application.interfaces import PasswordHasher
from project.app_auth.application.schemas import (
    LoginSchema,
    ProfileUpdate,
    UserRead,
)
from project.app_auth.domain.exceptions import (
    AuthenticationError,
    UserNotFound,
)
from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_auth.infrastructure.unit_of_work import SAAuthUnitOfWork
from project.core.log_config import get_logger

logger = get_logger(__name__)


class UserService:
    """Application service for managing users."""

    def __init__(self, uow: SAAuthUnitOfWork) -> None:
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
        if not any((user_id, email)):
            raise ValueError(
                "The method must receive one of the values ​​user_id or email."
            )

        unique_identifier: uuid.UUID | str | None = None
        user: User | None = None

        if user_id:
            unique_identifier = user_id
            user = await self.uow.users.get_by_id(user_id)
        elif email:
            unique_identifier = email
            user = await self.uow.users.get_by_email(email)

        if not user:
            logger.warning("User '%s' not found in DB", unique_identifier)
            raise UserNotFound(user_id, email)
        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID."""
        async with self.uow:
            return await self.uow.users.get_by_id(user_id)

    async def get_by_id_detail(self, user_id: uuid.UUID) -> User | None:
        """Get the user by ID. Load related objects."""
        async with self.uow:
            return await self.uow.users.get_by_id_detail(user_id)

    async def get_by_id_with_role(self, user_id: uuid.UUID) -> User | None:
        """Get the user by ID. Load related role."""
        async with self.uow:
            return await self.uow.users.get_by_id_role(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        async with self.uow:
            return await self.uow.users.get_by_email(email)

    async def get_by_email_detail(self, email: str) -> User | None:
        """Get user by email. Load relations."""
        async with self.uow:
            return await self.uow.users.get_by_email_detail(email)

    async def get_all_users(self, offset: int, limit: int) -> list[UserRead]:
        """Get all users from DB.

        Returns:
            list[UserRead]: All users as pydantic schemas.
        """
        async with self.uow:
            users = await self.uow.users.list_all(offset, limit)
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
                logger.warning("User with id '%s' not found", user_id)
                raise UserNotFound(user_id=user_id)

            update_data: dict = data.model_dump(exclude_unset=True)

            for field_name, field_value in update_data.items():
                setattr(user.profile, field_name, field_value)

            if update_data:
                await self.uow.commit()
                await self.uow.refresh(user, attribute_names=["profile"])
                logger.debug(
                    "User instance '%s' refreshed after update.", user_id
                )
            return user

    async def restore_user(self, credentials: LoginSchema) -> User:
        """Restore deactivated user.

        Args:
            credentials (LoginSchema): User credentials as pydantic schema.

        Returns:
            User: User instance with loaded relationships.
        """
        async with self.uow as uow:
            user: User | None = await uow.users.get_by_email_detail(
                email=credentials.username,
            )
            if not user:
                # email не найден в БД
                raise UserNotFound(email=credentials.username)

            psw_hasher: PasswordHasher = get_password_hasher()
            check_password: bool = psw_hasher.verify_password(
                plain_pswrd=credentials.password,
                stored_pswrd=user.hashed_password,
            )
            if not check_password:
                # введен неверный пароль
                logger.info(
                    "User '%s' entered a wrong password to recover the account",  # noqa
                    credentials.username,
                )
                raise AuthenticationError()

            if user.is_active:
                # пользователь уже активен
                return user

            # активация пользователя, сохранение изменений
            user.activate()
            await uow.commit()
            await uow.refresh(user)
            logger.info("User '%s' restored", credentials.username)
            return user

    async def revoke_role(self, user_id: uuid.UUID) -> User:
        """Revoke a role from a user."""
        async with self.uow as uow:
            user: User | None = await uow.users.get_by_id(user_id)
            if not user:
                raise UserNotFound(user_id=user_id)

            if user.role_id:
                user.role_id = None
                await uow.commit()
                await uow.refresh(user)
                logger.info("Role revoked from user '%s'", user_id)

            return user
