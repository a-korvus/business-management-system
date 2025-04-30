"""Important services in the 'app_auth' app."""

import uuid

from project.app_auth.application.interfaces import (
    AbstractUnitOfWork,
    PasswordHasher,
)
from project.app_auth.application.schemas import (
    LoginSchema,
    ProfileUpdate,
    Token,
    UserCreate,
    UserRead,
)
from project.app_auth.application.security import create_access_token
from project.app_auth.domain.exceptions import (
    AuthenticationError,
    EmailAlreadyExists,
    InvalidPasswordFormatError,
    UserNotFound,
)
from project.app_auth.domain.models import User
from project.core.log_config import get_logger

logger = get_logger(__name__)


class AuthService:
    """Application service for managing users authentication."""

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        hasher: PasswordHasher,
    ) -> None:
        """Initialize the service object. Set UoW and password hasher."""
        self.uow = uow
        self.hasher = hasher

    async def register_user(self, user_data: UserCreate) -> UserRead:
        """Register a new user.

        Args:
            user_data (UserCreate): New user data as pydantic schema.

        Raises:
            EmailAlreadyExists: If the email alrady exists in DB.

        Returns:
            UserRead: Schema of the new user object.
        """
        async with self.uow:  # UoW управляет транзакцией
            existing_user = await self.uow.users.get_by_email(user_data.email)
            if existing_user:
                raise EmailAlreadyExists(user_data.email)

            # создание доменного объекта User, хэширование внтури __init__
            new_user = User(
                email=user_data.email,
                plain_password=user_data.password,
                hasher=self.hasher,
            )

            # обновляем профиль, если переданы данные
            if user_data.profile:
                profile_data = user_data.profile.model_dump(exclude_unset=True)
                new_user.profile.update_profile(**profile_data)

            # добавляем объект в сессию через репозиторий
            await self.uow.users.add(new_user)
            await self.uow.commit()  # коммит транзакции через uow

            # возвращаем pydantic схему обновленного объекта
            return UserRead.model_validate(new_user)

    async def authenticate_user(self, credentials: LoginSchema) -> Token:
        """Authenticate the user.

        Args:
            credentials (LoginSchema): User credentials as pydantic schema.

        Raises:
            AuthenticationError: Email is missing from the database.
            AuthenticationError: User is disabled.
            AuthenticationError: Hash of the entered password doesn't match
                the hash in the database.
            AuthenticationError: Hash in the database is corrupted or
                in an old format.

        Returns:
            Token: New valid JWT token.
        """
        # на чтение необязательно открывать транзакцию,
        # uow используется для удобства и консистентности
        async with self.uow:
            user = await self.uow.users.get_by_email(credentials.username)
            if not user:
                raise AuthenticationError("Incorrect email.")
            if not user.is_active:
                raise AuthenticationError("User inactive.")

            try:
                if not user.check_password(credentials.password, self.hasher):
                    raise AuthenticationError("Incorrect password.")
            except InvalidPasswordFormatError as e:
                # если хэш в БД поврежден или в старом формате
                logger.exception("Error verifying password for %s", user.email)
                raise AuthenticationError(
                    "Authentication failed due to internal error"
                ) from e

        # генерация JWT токена
        access_token: str = create_access_token(
            data={"sub": user.email, "uid": str(user.id)}
        )
        return Token(access_token=access_token, token_type="bearer")


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

    async def update_user_profile(
        self,
        user_id: uuid.UUID,
        profile_data: ProfileUpdate,
    ) -> UserRead | None:
        """Update user profile."""
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise UserNotFound(user_id=user_id)

            update_data = profile_data.model_dump(exclude_unset=True)
            if update_data:
                user.profile.update_profile(**update_data)
                await self.uow.commit()

            return UserRead.model_validate(user)
