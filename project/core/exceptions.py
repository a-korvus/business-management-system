"""Custom exeptions to use in the project."""

from fastapi import HTTPException, status


class DomainError(Exception):
    """Base class for domain model exeptions."""

    ...


class OperatingDataException(HTTPException):
    """HTTP exception idicates incorrect operating data."""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "Incorrect operating data.",
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the HTTP exception."""
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers,
        )
