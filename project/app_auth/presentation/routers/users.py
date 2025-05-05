"""Users router in the 'app_auth'."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from project.app_auth.application.schemas import (
    ProfileUpdate,
    TokenData,
    UserDetail,
    UserRead,
)
from project.app_auth.application.services.users import UserService
from project.app_auth.domain.models import User
from project.app_auth.presentation.dependencies import (
    get_current_user,
    get_current_user_data,
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
    response_model=UserDetail,
    name="identity",
    summary="Get current user.",
    description="Return the details of the currently authenticated user.",
)
async def get_personal_data(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Return data of the current user. Protected endpoint.

    Args:
        current_user (Annotated[UserRead, Depends): Dependency to get
            current user. Requires a valid token in headers.

    Returns:
        User: Full User object.
    """
    return current_user


@router.put(
    path="/me/update-profile/",
    response_model=UserDetail,
    summary="Update current user.",
    description="Return the details of the currently authenticated user.",
)
async def update_personal_data(
    update_data: ProfileUpdate,
    token_data: Annotated[TokenData, Depends(get_current_user_data)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    """Update user profile. Protected endpoint."""
    user_id = uuid.UUID(token_data.uid)
    return await user_service.update_profile(user_id, update_data)


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
