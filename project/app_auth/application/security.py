"""Generate and validate JWT access tokens in the 'app_auth' app."""

import time
from datetime import datetime, timedelta, timezone
from typing import Any

from authlib.jose import JsonWebToken, JWTClaims, jwt
from authlib.jose.errors import (
    ExpiredTokenError,
    InvalidClaimError,
    JoseError,
    MissingClaimError,
)

from project.app_auth.application.schemas import TokenData
from project.app_auth.presentation.exceptions import CredentialException
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)

jwt_validator = JsonWebToken(algorithms=[settings.AUTH.JWT_ALGORITHM])


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT using Authlib.

    Args:
        data (dict): Some useful data. 'sub' key required with user ID value.
        expires_delta (timedelta | None, optional): Token lifetime.
            Defaults to None.

    Returns:
        str: Decoded token as a string.
    """
    if "sub" not in data:
        logger.exception("Missing 'sub' in token.")
        raise CredentialException(
            detail="Token data doesn't contain key 'sub'"
        )

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.AUTH.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    header: dict = {
        "alg": settings.AUTH.JWT_ALGORITHM,
        "typ": settings.AUTH.JWT_TYPE,
    }
    payload: dict = {
        "iss": settings.AUTH.JWT_ISSUER,  # кто создал и подписал токен
        "aud": settings.AUTH.JWT_AUDIENCE,  # кто получает токен
        "exp": int(expire.timestamp()),  # время истечения срока действия
        "iat": int(time.time()),  # время выпуска токена
        **to_encode,  # добавляем 'sub', 'uid' и другие данные
    }

    token_b: bytes = jwt.encode(header, payload, settings.AUTH.JWT_SECRET_KEY)
    return token_b.decode(encoding="utf-8")


def decode_access_token(token: str) -> TokenData | None:
    """Decode and validate JWT.

    Args:
        token (str): Received JWT.

    Returns:
        TokenData | None: TokenData if JWT valid of None if invalid.
    """
    claims_options: dict[str, dict[str, Any]] = {
        "iss": {"essential": True, "value": settings.AUTH.JWT_ISSUER},
        "aud": {"essential": True, "value": settings.AUTH.JWT_AUDIENCE},
        "sub": {"essential": True},
        "uid": {"essential": True},
    }

    try:
        # декодирование токена и проверка подписи (с ограничением алгоритма!)
        claims: JWTClaims = jwt_validator.decode(
            s=token,
            key=settings.AUTH.JWT_SECRET_KEY,
            claims_options=claims_options,
        )

        # валидация временных утверждений (exp, nbf, iat) с допуском 60 сек
        claims.validate(leeway=settings.AUTH.JWT_LEEWAY)
    except ExpiredTokenError:
        logger.info("Token expired.")
        return None
    except MissingClaimError:
        logger.exception("Missing claim in token")
        raise CredentialException(detail="Missing required claim in token")
    except InvalidClaimError as e:
        logger.warning("Invalid assertion in token: %s", e)
        return None
    except JoseError:
        logger.exception("JOSE error validating token")
        raise CredentialException()

    token_data = TokenData.model_validate(claims)
    logger.info("Token data validated successfully.")
    return token_data
