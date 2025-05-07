"""Presentation related exceptions."""

from fastapi import HTTPException, status


class AccessRightsError(HTTPException):
    """HTTP exception idicates incorrect user role to access."""

    def __init__(
        self,
        status_code: int = status.HTTP_403_FORBIDDEN,
        detail: str = "Insufficient access rights.",
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the HTTP exception."""
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers,
        )
