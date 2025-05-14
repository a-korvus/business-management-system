"""Project exception handlers."""

from fastapi import status
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse

from project.app_auth.domain.exceptions import UserNotFound
from project.app_org.domain.exceptions import CommandNotFound, RoleNotFound


async def user_not_found_exc_handler(
    _rq: Request,
    exc: Exception,
) -> ORJSONResponse:
    """Handle the UserNotFound exception at the application level."""
    return ORJSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def command_not_found_exc_handler(
    _rq: Request,
    exc: Exception,
) -> ORJSONResponse:
    """Handle the CommandNotFound exception at the application level."""
    return ORJSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def role_not_found_exc_handler(
    _rq: Request,
    exc: Exception,
) -> ORJSONResponse:
    """Handle the RoleNotFound exception at the application level."""
    return ORJSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


exc_handlers = {
    UserNotFound: user_not_found_exc_handler,
    CommandNotFound: command_not_found_exc_handler,
    RoleNotFound: role_not_found_exc_handler,
}
