"""Users router in the 'app_auth'."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from project.app_auth.application.schemas import (
    LoginSchema,
    ProfileUpdate,
    UserCreate,
    UserDetail,
    UserRead,
)
from project.app_auth.application.services.users import UserService
from project.app_auth.domain.exceptions import (
    AuthenticationError,
    EmailAlreadyExists,
)
from project.app_auth.domain.models import User
from project.app_auth.presentation.dependencies import (
    get_admin,
    get_current_user,
    get_token_data,
    get_user_service,
)
from project.app_auth.presentation.exceptions import CredentialException
from project.app_org.application.schemas import AssignRolePayload
from project.config import settings
from project.core.exceptions import OperatingDataException
from project.core.log_config import get_logger
from project.core.service import CoreService, get_core_service

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
    description="Return the details of the current authenticated user.",
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
    path="/me/",
    response_model=UserDetail,
    summary="Update current user.",
    description="Return the details of the currently authenticated user.",
)
async def update_personal_data(
    update_data: ProfileUpdate,
    token_data: Annotated[dict, Depends(get_token_data)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    """Update user profile. Protected endpoint."""
    return await user_service.update_profile(token_data["uid"], update_data)


@router.delete(
    path="/me/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate current user.",
    description="Deactivate current user. "
    "Then run permanent deletion after 30 days.",
)
async def deactivate_user(
    token_data: Annotated[dict, Depends(get_token_data)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    """Deactivate user. Protected endpoint."""
    await user_service.deactivate_user(user_id=token_data["uid"])


@router.post(
    path="/me/",
    response_model=UserDetail,
    summary="Restore user.",
    description="Restore and return user if it exists and"
    "was deactivated earlier.",
)
async def restore_user(
    credentials: LoginSchema,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    """Restore user if deactivate earlier."""
    try:
        return await user_service.restore_user(credentials)
    except AuthenticationError as e:
        logger.error(
            "Authentication failed. Email: '%s', reason: '%s",
            credentials.username,
            str(e),
        )
        raise CredentialException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is invalid.",
        )


@router.get("/", response_model=list[UserRead])
async def get_list_all_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> list[UserRead]:
    """Get the list of all users from DB.

    Args:
        user_service (Annotated[UserService, Depends): App User service.

    Returns:
        list[UserRead]: All users data.
    """
    return await user_service.get_all_users()


@router.get(path="/{user_id}/", response_model=UserDetail)
async def get_user_detail(
    user_id: Annotated[uuid.UUID, Path(description="Existing user ID")],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    """Get the user from DB with all related models."""
    user = await user_service.get_by_id_detail(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' doesn't exist.",
        )
    return user


@router.post(
    path="/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
)
async def create_user(
    core_service: Annotated[CoreService, Depends(get_core_service)],
    create_schema: UserCreate,
    admin: Annotated[User, Depends(get_admin)],
) -> User:
    """Create a new user. Protected. For admins only."""
    try:
        return await core_service.create_user(schema=create_schema)
    except EmailAlreadyExists as e:
        raise OperatingDataException(detail=str(e))


@router.put(
    path="/{user_id}/",
    status_code=status.HTTP_200_OK,
    response_model=UserDetail,
)
async def update_profile(
    user_id: uuid.UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
    updating_data: ProfileUpdate,
    admin: Annotated[User, Depends(get_admin)],
) -> User:
    """Update a user profile. Protected. For admins only."""
    return await user_service.update_profile(user_id, updating_data)


@router.patch(
    path="/{user_id}/role/",
    status_code=status.HTTP_200_OK,
    response_model=UserRead,
)
async def assign_user_role(
    user_id: Annotated[uuid.UUID, Path(description="Existing user ID")],
    role_payload: AssignRolePayload,
    core_service: Annotated[CoreService, Depends(get_core_service)],
    admin: Annotated[User, Depends(get_admin)],
) -> User:
    """Assign a role to a user. Protected. For admins only."""
    return await core_service.assign_user_role(
        user_id=user_id,
        role_id=role_payload.role_id,
    )


@router.delete(
    path="/{user_id}/role/",
    response_model=UserRead,
)
async def revoke_user_role(
    user_id: Annotated[uuid.UUID, Path(description="Existing user ID")],
    user_service: Annotated[UserService, Depends(get_user_service)],
    admin: Annotated[User, Depends(get_admin)],
) -> User:
    """Revoke a role from a user. Protected. For admins only."""
    return await user_service.revoke_role(user_id)
