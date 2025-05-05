"""Auth router in the 'app_auth'."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from project.app_auth.application.schemas import (
    LoginSchema,
    Token,
    UserCreate,
    UserRead,
)
from project.app_auth.application.services.auth import AuthService
from project.app_auth.domain.exceptions import (
    AuthenticationError,
    EmailAlreadyExists,
    InvalidPasswordFormatError,
)
from project.app_auth.presentation.dependencies import get_auth_service
from project.app_org.domain.exceptions import CommandNotFound
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix=settings.AUTH.PREFIX_AUTH,
    tags=["users", "authentication"],
)


@router.post(
    path="/register/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user.",
    description="Create a new user account with email and password.",
)
async def register(
    user_in: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    """Self-registration of a new user in the system.

    Args:
        user_in (UserCreate): User input data.
        auth_service (Annotated[AuthService, Depends): App Auth service.

    Raises:
        HTTPException: If email already in use.
        HTTPException: If some domain error occured.
        HTTPException: Unexpected error.

    Returns:
        UserRead: Data of the new saved user.
    """
    try:
        return await auth_service.register_user(user_data=user_in)
    except EmailAlreadyExists as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except CommandNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:  # ошибки валидации из домена
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:  # любые непредвиденные ошибки # noqa
        logger.exception("Unexpected error during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred during registartion.",
        )


@router.post(
    path="/login/",
    response_model=Token,
    summary="Login for access token.",
    description="Authenticate user with email and password "
    "(sent as form data) and returns an access token.",
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """Authenticate the user by email and password."""
    try:
        login_credentials = LoginSchema(
            username=form_data.username,
            password=form_data.password,
        )
        return await auth_service.authenticate_user(
            credentials=login_credentials,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},  # заголовок для OAuth2
        )
    except InvalidPasswordFormatError:  # если хэш в БД невалиден
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to an internal server error.",
        )
    except Exception as e:  # noqa
        logger.exception("Unexpected erroe during login.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occerred during login.",
        )
