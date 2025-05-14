"""Authentication backend for SQLAdmin."""

from typing import Literal

from sqladmin.authentication import AuthenticationBackend
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from project.app_auth.application.interfaces import PasswordHasher
from project.app_auth.application.services.users import UserService
from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_auth.presentation.dependencies import get_uow
from project.app_org.application.enums import RoleType
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)


class AdminAuth(AuthenticationBackend):
    """Custom authentication backend."""

    async def login(self, request: Request) -> bool:
        """Handle the login form submission."""
        user_service = UserService(uow=get_uow())
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        if not isinstance(email, str) or not isinstance(password, str):
            logger.warning("Username or password missing.")
            return False

        # get User
        user: User | None = await user_service.get_by_email_deatil(email)
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

        user_command: str | None
        if user.command:
            user_command = user.command.name
        access_rights: bool = any(
            (
                user.email == settings.MASTER_EMAIL,
                user_command == settings.MASTER_COMMAND_NAME,
                user.role
                in (
                    RoleType.ADMINISTRATOR,
                    RoleType.HEAD_OF_DEPARTMENT,
                ),
            )
        )
        if not access_rights:
            return False

        # save in session important User data
        request.session.update(
            {
                "user_id": str(user.id),
                "access_rights": access_rights,
            }
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
        elif not request.session.get("access_rights"):
            return RedirectResponse(
                url=request.url_for("admin:login"),
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return True


authentication_backend = AdminAuth(secret_key=settings.ADMIN_SECRET_KEY)
