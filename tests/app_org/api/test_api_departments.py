"""Test API routs for 'departments' router."""

import random

import pytest
from httpx import AsyncClient, Response

from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]

ORG_PREFIX = settings.PREFIX_ORG


async def test_create_department(
    httpx_test_client: AsyncClient,
    fake_department_data: dict,
) -> None:
    """Test creating a new department."""
    response: Response = await httpx_test_client.post(
        url=f"{ORG_PREFIX}/departments/",
        json=fake_department_data,
    )

    assert response.status_code == 201

    response_data = response.json()

    assert isinstance(response_data, dict)
    assert response_data.get("id") is not None
    assert response_data.get("name") == fake_department_data["name"]
    assert response_data.get("description") == fake_department_data.get(
        "description"
    )
    assert response_data.get("command_id") == fake_department_data.get(
        "command_id"
    )


async def test_get_departments(
    httpx_test_client: AsyncClient,
    fake_department_data: dict,
) -> None:
    """Test retrieving all departments."""
    departments_count = 0
    for _ in range(random.randint(10, 20)):
        response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/departments/",
            json=fake_department_data,
        )

        assert response_create.status_code == 201

        departments_count += 1

    response_get: Response = await httpx_test_client.get(
        url=f"{ORG_PREFIX}/departments/",
    )
    response_data = response_get.json()

    assert isinstance(response_data, list)
    assert departments_count == len(response_data)
    for department in response_data:
        assert isinstance(department, dict)
        assert department.get("id") is not None


async def test_get_specific_department(
    httpx_test_client: AsyncClient,
    fake_department_data: dict,
) -> None:
    """Test retrieving the department."""
    departments = list()
    for _ in range(random.randint(10, 20)):
        response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/departments/",
            json=fake_department_data,
        )

        assert response_create.status_code == 201

        response_create_data = response_create.json()

        assert isinstance(response_create_data, dict)

        departments.append(response_create_data)

    for department in departments:
        department_id = department.get("id")

        assert department_id is not None

        response_get = await httpx_test_client.get(
            url=f"{ORG_PREFIX}/departments/{department_id}/",
        )

        assert response_get.status_code == 200

        response_get_data = response_get.json()

        assert isinstance(response_get_data, dict)
        assert response_get_data.get("id") == department_id
        assert response_get_data.get("created_at") is not None
        assert response_get_data.get("updated_at") is not None


async def test_update_department(
    httpx_test_client: AsyncClient,
    fake_department_data: dict,
) -> None:
    """Test updating the department."""
    departments = list()
    for _ in range(random.randint(10, 20)):
        response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/departments/",
            json=fake_department_data,
        )

        assert response_create.status_code == 201

        response_create_data = response_create.json()

        assert isinstance(response_create_data, dict)

        departments.append(response_create_data)

    updating_data = {
        "description": fake_department_data["description"][:-100],
    }
    some_existing_department: dict = random.choice(departments)
    some_department_id = some_existing_department.get("id")

    assert some_department_id is not None

    response_update = await httpx_test_client.put(
        url=f"{ORG_PREFIX}/departments/{some_department_id}/",
        json=updating_data,
    )

    assert response_update.status_code == 200

    response_update_data = response_update.json()

    assert isinstance(response_update_data, dict)
    assert some_department_id == response_update_data.get("id")
    assert some_existing_department.get(
        "description"
    ) != response_update_data.get("description")
    assert updating_data.get("description") == response_update_data.get(
        "description"
    )
