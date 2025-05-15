"""Auxiliary test functions."""

from httpx import AsyncClient

from project.config import settings


async def get_auth_token(
    httpx_client: AsyncClient,
    email: str,
    password: str,
) -> str:
    """Get authentication token."""
    response = await httpx_client.post(
        url=f"{settings.AUTH.PREFIX_AUTH}/login/",
        data={"username": email, "password": password},
    )
    response.raise_for_status()
    return response.json()["access_token"]
