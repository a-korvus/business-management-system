"""Presentation related exceptions."""

from fastapi import HTTPException, status


class CredentialException(HTTPException):
    """HTTP exception indicates incorrect user credentials."""

    def __init__(
        self,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail: str = "Could not validate credentials.",
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the HTTP exception."""
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}

        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers,
        )
