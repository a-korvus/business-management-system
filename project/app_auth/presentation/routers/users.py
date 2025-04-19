"""Users router in the 'app_auth'."""

from typing import Annotated

from fastapi import APIRouter, Depends

from project.app_auth.application.schemas import UserRead
from project.app_auth.config import auth_config
from project.app_auth.presentation.dependencies import get_current_user
from project.core.log_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix=auth_config.APP_AUTH_PREFIX_USERS,
    tags=["Users"],
)


@router.get(
    path="/me",
    response_model=UserRead,
    summary="Get current user.",
    description="Return the details of the currently authenticated user.",
)
async def read_users_me(
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    """
    Return data of the current user.

    Args:
        current_user (Annotated[UserRead, Depends): Dependency to get
            current user. Requires a valid token in headers.

    Returns:
        UserRead: User data.
    """
    return current_user
