"""Test API routs for 'users' router."""

from typing import Any

import pytest
from httpx import AsyncClient, Response

from project.config import settings

USERS_PREFIX = settings.AUTH.PREFIX_USERS

pytestmark = pytest.mark.anyio


@pytest.mark.usefixtures("truncate_tables")
async def test_read_users_me(
    httpx_test_client: AsyncClient,
    authenticated_user: dict[str, Any],
) -> None:
    """Test get user personal data. Protected endpoint."""
    token = authenticated_user["token"]
    expected_user_data = authenticated_user["user"]
    headers = {"Authorization": f"Bearer {token}"}

    response: Response = await httpx_test_client.get(
        url=f"{USERS_PREFIX}/me/",
        headers=headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == expected_user_data["id"]
    assert response_data["email"] == expected_user_data["email"]
    assert response_data["is_active"] == expected_user_data["is_active"]


@pytest.mark.usefixtures("truncate_tables")
async def test_read_users_me_no_token(httpx_test_client: AsyncClient) -> None:
    """Test get user personal data without token."""
    response: Response = await httpx_test_client.get(url=f"{USERS_PREFIX}/me/")
    assert response.status_code == 401


@pytest.mark.usefixtures("truncate_tables")
async def test_read_users_me_invalid_token(
    httpx_test_client: AsyncClient,
) -> None:
    """Test get user personal data with invalid token."""
    response: Response = await httpx_test_client.get(
        url=f"{USERS_PREFIX}/me/",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401


@pytest.mark.usefixtures("truncate_tables")
async def test_list_users(
    httpx_test_client: AsyncClient,
    authenticated_user: dict[str, Any],
) -> None:
    """Test get list of users."""
    response: Response = await httpx_test_client.get(f"{USERS_PREFIX}/list/")

    assert response.status_code == 200

    user_list = response.json()

    assert isinstance(user_list, list)
    assert len(user_list) == 1

    user_data = user_list.pop()

    assert isinstance(user_data, dict)
    assert authenticated_user["user"]["id"] == user_data["id"]
    assert authenticated_user["user"]["email"] == user_data["email"]
