"""Auth-related service in 'app_auth'."""

from project.app_auth.application.interfaces import (
    AbstractUnitOfWork,
    PasswordHasher,
)
from project.app_auth.application.schemas import (
    LoginSchema,
    Token,
    UserCreate,
    UserRead,
)
from project.app_auth.application.security import create_access_token
from project.app_auth.domain.exceptions import (
    AuthenticationError,
    EmailAlreadyExists,
    InvalidPasswordFormatError,
)
from project.app_auth.domain.models import User
from project.app_org.domain.exceptions import CommandNotFound
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
        async with self.uow as uow:  # UoW управляет транзакцией
            existing_user = await uow.users.get_by_email(user_data.email)
            if existing_user:
                raise EmailAlreadyExists(user_data.email)

            if user_data.command_id:
                if not await uow.users.check_command_exists(
                    command_id=user_data.command_id,
                ):
                    raise CommandNotFound(command_id=user_data.command_id)

            # создание доменного объекта User, хэширование внтури __init__
            new_user = User(
                email=user_data.email,
                plain_password=user_data.password,
                command_id=user_data.command_id,
                hasher=self.hasher,
            )

            # добавляем объект в сессию через репозиторий
            await uow.users.add(new_user)
            await uow.commit()  # коммит транзакции через uow
            await uow.refresh(new_user)
            logger.debug(
                "User instance '%s' refreshed after creating.",
                new_user.id,
            )
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
        async with self.uow as uow:
            user = await uow.users.get_by_email(credentials.username)
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
