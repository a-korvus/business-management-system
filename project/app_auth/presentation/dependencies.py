"""Dependencies in the 'app_auth' app."""

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from project.app_auth.application.interfaces import (
    AbstractUnitOfWork,
    PasswordHasher,
)
from project.app_auth.application.schemas import TokenData, UserRead
from project.app_auth.application.security import decode_access_token
from project.app_auth.application.services import AuthService, UserService
from project.app_auth.config import auth_config
from project.app_auth.infrastructure.security import password_hasher
from project.app_auth.infrastructure.unit_of_work import SAUnitOfWork
from project.app_auth.presentation.exceptions import CredentialException
from project.core.log_config import get_logger

logger = get_logger(__name__)


def get_uow() -> AbstractUnitOfWork:
    """Get Unit of Work instance."""
    # фабрику сессий получаем в конструкторе класса по умолчанию
    return SAUnitOfWork()


def get_password_hasher() -> PasswordHasher:
    """Get the only one password hasher instance."""
    return password_hasher  # синглтон


def get_auth_service(
    uow: Annotated[AbstractUnitOfWork, Depends(get_uow)],
    hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
) -> AuthService:
    """Get authentication service instance."""
    return AuthService(uow=uow, hasher=hasher)


def get_user_service(
    uow: Annotated[AbstractUnitOfWork, Depends(get_uow)],
) -> UserService:
    """Get user service instance."""
    return UserService(uow=uow)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{auth_config.APP_AUTH_PREFIX_AUTH}/login/",
)


async def get_current_user_data(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TokenData:
    """Decode the token and get data from it."""
    token_data = decode_access_token(token)

    if token_data is None or token_data.uid is None:
        raise CredentialException()

    return token_data


async def get_current_user(
    token_data: Annotated[TokenData, Depends(get_current_user_data)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    """
    Get current user from DB based on token data.

    Args:
        token_data (Annotated[TokenData, Depends): Token data as schema.
        user_service (Annotated[UserService, Depends): App User service.

    Raises:
        CredentialException: User not found in DB.
        CredentialException: User exists but inactive.
        CredentialException: UUID is invalid.

    Returns:
        UserRead: User data as pydantic schema.
    """
    try:
        user_id = uuid.UUID(token_data.uid)
        user: UserRead | None = await user_service.get_user_by_id(user_id)

        if user is None:
            raise CredentialException(
                detail="Could not validate credentials (user not found)"
            )
        elif not user.is_active:
            raise CredentialException(
                detail="Could not validate credentials (user inactive)"
            )

        return user
    except ValueError:  # ValueError если UUID невалидный
        logger.exception("UUID invalid: %s", user_id)
        raise CredentialException()
