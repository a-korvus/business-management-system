"""Test API routs for 'users' router."""

from json.decoder import JSONDecodeError
from typing import Any

import pytest
from faker import Faker
from httpx import AsyncClient, Response

from project.app_auth.application.schemas import UserCreate
from project.config import settings

USERS_PREFIX = settings.AUTH.PREFIX_USERS
AUTH_PREFIX = settings.AUTH.PREFIX_AUTH

pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]


async def test_get_personal_data(
    httpx_test_client: AsyncClient,
    authenticated_user: dict[str, Any],
) -> None:
    """Test retrieving user personal data. Protected."""
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
    assert expected_user_data.get("profile") is None
    assert isinstance(response_data["profile"], dict)


async def test_update_personal_data(
    httpx_test_client: AsyncClient,
    authenticated_user: dict[str, Any],
    fake_instance: Faker,
) -> None:
    """Test updating user profile. Protected."""
    token = authenticated_user["token"]
    expected_user_data = authenticated_user["user"]
    headers = {"Authorization": f"Bearer {token}"}

    upd_profile_data = {
        "first_name": fake_instance.first_name(),
        "bio": fake_instance.text(max_nb_chars=255),
    }

    response: Response = await httpx_test_client.put(
        url=f"{USERS_PREFIX}/me/update-profile/",
        headers=headers,
        json=upd_profile_data,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, dict)
    assert "id" in response_data
    assert response_data["id"] == expected_user_data["id"]

    profile = response_data.get("profile")

    assert isinstance(profile, dict)
    assert profile.get("first_name") == upd_profile_data["first_name"]
    assert profile.get("bio") == upd_profile_data["bio"]
    assert profile.get("last_name") is None


async def test_deactivate_user(
    httpx_test_client: AsyncClient,
    authenticated_user: dict[str, Any],
) -> None:
    """Test deactivating user. Protected."""
    token = authenticated_user["token"]
    headers = {"Authorization": f"Bearer {token}"}

    response: Response = await httpx_test_client.delete(
        url=f"{USERS_PREFIX}/me/",
        headers=headers,
    )

    assert response.status_code == 204
    with pytest.raises(JSONDecodeError):
        response.json()


async def test_restore_user(
    httpx_test_client: AsyncClient,
    fake_user_schema: UserCreate,
) -> None:
    """Test restoring deactivated user."""
    # создать пользователя
    create_response: Response = await httpx_test_client.post(
        url=f"{AUTH_PREFIX}/register/",
        json=fake_user_schema.model_dump(),
    )
    assert create_response.status_code == 201
    new_user_data: dict = create_response.json()
    assert new_user_data.get("id") is not None

    # получить токен
    auth_response = await httpx_test_client.post(
        url=f"{AUTH_PREFIX}/login/",
        data={
            "username": fake_user_schema.email,
            "password": fake_user_schema.password,
        },
    )
    assert auth_response.status_code == 200
    token: str = auth_response.json()["access_token"]

    # деактивировать пользователя
    deactivate_response: Response = await httpx_test_client.delete(
        url=f"{USERS_PREFIX}/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert deactivate_response.status_code == 204

    # восстановить пользователя (активировать)
    credentials = {
        "username": fake_user_schema.email,
        "password": fake_user_schema.password,
    }
    restore_response: Response = await httpx_test_client.post(
        url=f"{USERS_PREFIX}/restore/",
        json=credentials,
    )

    assert restore_response.status_code == 200

    restore_data = restore_response.json()
    assert isinstance(restore_data, dict)
    assert restore_data.get("id") == new_user_data.get("id")
    assert isinstance(restore_data.get("profile"), dict)
    assert not restore_data.get("command")
    assert not restore_data.get("role")


async def test_read_users_me_no_token(httpx_test_client: AsyncClient) -> None:
    """Test get user personal data without token."""
    response: Response = await httpx_test_client.get(url=f"{USERS_PREFIX}/me/")
    assert response.status_code == 401


async def test_read_users_me_invalid_token(
    httpx_test_client: AsyncClient,
) -> None:
    """Test get user personal data with invalid token."""
    response: Response = await httpx_test_client.get(
        url=f"{USERS_PREFIX}/me/",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401


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
