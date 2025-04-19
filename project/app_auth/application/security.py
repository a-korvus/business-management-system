"""Generate and validate JWT access tokens in the 'app_auth' app."""

from datetime import datetime, timedelta, timezone

import jwt

from project.app_auth.application.schemas import TokenData
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.AUTH.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # issued at; время выдачи токена
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(
        payload=to_encode,
        key=settings.AUTH.SECRET_KEY,
        algorithm=settings.AUTH.ALGORITHM,
    )


def decode_access_token(token: str) -> TokenData | None:
    """Decode JWT access token."""
    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.AUTH.SECRET_KEY,
            algorithms=[settings.AUTH.ALGORITHM],
            options={"require": ["exp", "sub", "uid"]},  # обязательные поля
        )
        return TokenData.model_validate(payload)
    except jwt.ExpiredSignatureError:
        logger.exception("Token has expired.")
        return None
    except jwt.InvalidTokenError:
        logger.exception("Invalid token")
        return None
