"""Test API routs for 'roles' router."""

import random

import pytest
from httpx import AsyncClient, Response

from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]

ORG_PREFIX = settings.PREFIX_ORG


async def test_create_role(
    httpx_test_client: AsyncClient,
    fake_role_data: dict,
) -> None:
    """Test creating a new role."""
    response: Response = await httpx_test_client.post(
        url=f"{ORG_PREFIX}/roles/",
        json=fake_role_data,
    )

    assert response.status_code == 201

    response_data = response.json()

    assert isinstance(response_data, dict)
    assert response_data.get("id") is not None
    assert response_data.get("name") == fake_role_data["name"]
    assert response_data.get("description") == fake_role_data["description"]
    assert response_data.get("department_id") == fake_role_data.get(
        "department_id"
    )


async def test_get_roles(
    httpx_test_client: AsyncClient,
    fake_role_data: dict,
) -> None:
    """Test retrieving all roles."""
    roles_count = 0
    for _ in range(random.randint(10, 20)):
        response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/roles/",
            json=fake_role_data,
        )

        assert response_create.status_code == 201

        roles_count += 1

    response_get: Response = await httpx_test_client.get(
        url=f"{ORG_PREFIX}/roles/",
    )
    response_data = response_get.json()

    assert isinstance(response_data, list)
    assert roles_count == len(response_data)
    for role in response_data:
        assert isinstance(role, dict)
        assert role.get("id") is not None


async def test_get_specific_role(
    httpx_test_client: AsyncClient,
    fake_role_data: dict,
) -> None:
    """Test retrieving the role."""
    roles = list()
    for _ in range(random.randint(10, 20)):
        response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/roles/",
            json=fake_role_data,
        )

        assert response_create.status_code == 201

        response_create_data = response_create.json()

        assert isinstance(response_create_data, dict)

        roles.append(response_create_data)

    for role in roles:
        role_id = role.get("id")

        assert role_id is not None

        response_get = await httpx_test_client.get(
            url=f"{ORG_PREFIX}/roles/{role_id}/",
        )

        assert response_get.status_code == 200

        response_get_data = response_get.json()

        assert isinstance(response_get_data, dict)
        assert response_get_data.get("id") == role_id
        assert response_get_data.get("created_at") is not None
        assert response_get_data.get("updated_at") is not None


async def test_update_role(
    httpx_test_client: AsyncClient,
    fake_role_data: dict,
) -> None:
    """Test updating the role."""
    roles = list()
    for _ in range(random.randint(10, 20)):
        response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/roles/",
            json=fake_role_data,
        )

        assert response_create.status_code == 201

        response_create_data = response_create.json()

        assert isinstance(response_create_data, dict)

        roles.append(response_create_data)

    updating_data = {
        "description": fake_role_data["description"][:-100],
    }
    some_existing_role: dict = random.choice(roles)
    some_role_id = some_existing_role.get("id")

    assert some_role_id is not None

    response_update = await httpx_test_client.put(
        url=f"{ORG_PREFIX}/roles/{some_role_id}/",
        json=updating_data,
    )

    assert response_update.status_code == 200

    response_update_data = response_update.json()

    assert isinstance(response_update_data, dict)
    assert some_role_id == response_update_data.get("id")
    assert some_existing_role.get("description") != response_update_data.get(
        "description"
    )
    assert updating_data.get("description") == response_update_data.get(
        "description"
    )
