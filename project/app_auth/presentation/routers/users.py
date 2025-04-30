"""Users router in the 'app_auth'."""

from typing import Annotated

from fastapi import APIRouter, Depends

from project.app_auth.application.schemas import UserRead
from project.app_auth.application.services import UserService
from project.app_auth.domain.models import User
from project.app_auth.presentation.dependencies import (
    get_current_user,
    get_user_service,
)
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix=settings.AUTH.PREFIX_USERS,
    tags=["users"],
)


@router.get(
    path="/me/",
    response_model=UserRead,
    name="identity",
    summary="Get current user.",
    description="Return the details of the currently authenticated user.",
)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Return data of the current user.

    Args:
        current_user (Annotated[UserRead, Depends): Dependency to get
            current user. Requires a valid token in headers.

    Returns:
        User: User object.
    """
    return current_user


@router.get("/list/", response_model=list[UserRead])
async def list_all_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> list[UserRead]:
    """Get the list of all users from DB.

    Args:
        user_service (Annotated[UserService, Depends): App User service.

    Returns:
        list[UserRead]: All users data.
    """
    return await user_service.get_all_users()
