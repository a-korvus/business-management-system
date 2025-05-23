"""Dependencies in the 'app_auth' app."""

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from project.app_auth.application.interfaces import PasswordHasher
from project.app_auth.application.schemas import TokenData
from project.app_auth.application.security import decode_access_token
from project.app_auth.application.services.auth import AuthService
from project.app_auth.application.services.users import UserService
from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_auth.infrastructure.unit_of_work import SAAuthUnitOfWork
from project.app_auth.presentation.exceptions import CredentialException
from project.app_org.application.enums import RoleType
from project.app_org.presentation.exceptions import AccessRightsError
from project.config import settings
from project.core.db.setup import AsyncSessionFactory
from project.core.log_config import get_logger

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.AUTH.PREFIX_AUTH}/login/",
)


def get_uow() -> SAAuthUnitOfWork:
    """Get Unit of Work instance."""
    # фабрику сессий получаем в конструкторе класса по умолчанию
    return SAAuthUnitOfWork(session_factory=AsyncSessionFactory)


def get_auth_service(
    uow: Annotated[SAAuthUnitOfWork, Depends(get_uow)],
    hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
) -> AuthService:
    """Get authentication service instance."""
    return AuthService(uow=uow, hasher=hasher)


def get_user_service(
    uow: Annotated[SAAuthUnitOfWork, Depends(get_uow)],
) -> UserService:
    """Get user service instance."""
    return UserService(uow=uow)


async def get_token_data(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    """Decode the token and get data from it."""
    token_data: TokenData | None = decode_access_token(token)

    if token_data is None or token_data.uid is None:
        raise CredentialException()

    token_data_dct: dict = token_data.model_dump()
    token_data_dct["uid"] = uuid.UUID(token_data_dct.pop("uid"))

    return token_data_dct


async def get_current_user(
    token_data: Annotated[dict, Depends(get_token_data)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    """Get current user from DB based on token data.

    Args:
        token_data (Annotated[dict, Depends): Token data as schema.
        user_service (Annotated[UserService, Depends): App User service.

    Raises:
        CredentialException: UUID is invalid.
        CredentialException: User not found in DB.
        CredentialException: User exists but inactive.

    Returns:
        User: User model object.
    """
    user_id = token_data["uid"]
    try:
        user: User | None = await user_service.get_by_id_detail(user_id)
    except ValueError:  # UUID невалидный
        logger.exception("UUID invalid: %s", user_id)
        raise CredentialException()

    if user is None:
        raise CredentialException(
            detail="Could not validate credentials (user not found)"
        )
    elif not user.is_active:
        raise CredentialException(
            detail="Could not validate credentials (user inactive)"
        )

    return user


async def get_admin(
    token_data: Annotated[dict, Depends(get_token_data)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    """Get current user from DB based on token data if he has admin role.

    Raises:
        AccessRightsError: If user isn't administrator.

    Returns:
        User: Authenticated user that has an admin role.
    """
    user_id = token_data["uid"]
    try:
        user: User | None = await user_service.get_by_id_detail(user_id)
    except ValueError:  # UUID невалидный
        logger.exception("UUID invalid: %s", user_id)
        raise CredentialException()

    if user is None:
        raise CredentialException(
            detail="Could not validate credentials (user not found)"
        )
    elif not user.is_active:
        raise CredentialException(
            detail="Could not validate credentials (user inactive)"
        )
    elif user.role != RoleType.ADMINISTRATOR and not user.command:
        raise AccessRightsError()
    elif (
        user.role != RoleType.ADMINISTRATOR
        and user.command is not None
        and user.command.name != settings.MASTER_COMMAND_NAME
    ):
        raise AccessRightsError()

    return user
