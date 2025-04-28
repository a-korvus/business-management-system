"""Authentication backend for SQLAdmin."""

from typing import Literal

from sqladmin.authentication import AuthenticationBackend
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from project.app_auth.application.interfaces import PasswordHasher
from project.app_auth.application.services import UserService
from project.app_auth.domain.models import User
from project.app_auth.presentation.dependencies import (
    get_password_hasher,
    get_uow,
)
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)


class AdminAuth(AuthenticationBackend):
    """Custom authentication backend."""

    _user_service = UserService(uow=get_uow())

    async def login(self, request: Request) -> bool:
        """Handle the login form submission."""
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        if not email or not password:
            logger.warning("Username or password missing.")
            return False
        email = str(email) if not isinstance(email, str) else email
        password = str(password) if not isinstance(password, str) else password

        # get User
        user: User | None = await self._user_service.get_user_by_email(email)
        if not user:
            logger.warning("User '%s' doesn't exist.", email)
            return False

        # validate password
        hasher: PasswordHasher = get_password_hasher()
        validate_pswd: bool = hasher.verify_password(
            plain_pswrd=password,
            stored_pswrd=user.hashed_password,
        )
        if not validate_pswd:
            return False

        # save in session inportant User data
        request.session.update(
            {"user_id": str(user.id)},
            # "user_role": user.role., ...
        )
        logger.debug("Admin session was successfully updated.")
        return True

    async def logout(self, request: Request) -> Literal[True]:
        """Handle logout from admin panel."""
        request.session.clear()
        logger.debug("AdminAuth 'logout' called")
        return True

    async def authenticate(self, request: Request) -> bool | RedirectResponse:
        """Check every incoming request."""
        if not request.session.get("user_id"):
            return RedirectResponse(
                url=request.url_for("admin:login"),
                status_code=status.HTTP_302_FOUND,
            )

        return True


authentication_backend = AdminAuth(secret_key=settings.ADMIN_SECRET_KEY)
