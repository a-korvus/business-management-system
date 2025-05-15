"""Test API routs for 'commands' router."""

import random

import pytest
from faker import Faker
from httpx import AsyncClient, Response

from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]

ORG_PREFIX = settings.PREFIX_ORG


async def test_create_command(
    httpx_test_client: AsyncClient,
    fake_command_data: dict,
    get_master_token: str,
) -> None:
    """Test creating a new command."""
    # unauthorized response
    response: Response = await httpx_test_client.post(
        url=f"{ORG_PREFIX}/commands/",
        json=fake_command_data,
    )

    assert response.status_code == 401

    # master authorized response
    master_response: Response = await httpx_test_client.post(
        url=f"{ORG_PREFIX}/commands/",
        json=fake_command_data,
        headers={"Authorization": f"Bearer {get_master_token}"},
    )

    assert master_response.status_code == 201

    response_data = master_response.json()

    assert isinstance(response_data, dict)
    assert response_data.get("id") is not None
    assert response_data.get("name") == fake_command_data["name"]
    assert response_data.get("description") == fake_command_data.get(
        "description"
    )


async def test_get_commands(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    get_master_token: str,
) -> None:
    """Test retrieving all commands."""
    commands_count = 0
    for _ in range(random.randint(10, 20)):
        master_response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/commands/",
            json={
                "name": fake_instance.unique.company(),
                "description": fake_instance.text(max_nb_chars=500),
            },
            headers={"Authorization": f"Bearer {get_master_token}"},
        )

        assert master_response_create.status_code == 201

        commands_count += 1

    response_get: Response = await httpx_test_client.get(
        url=f"{ORG_PREFIX}/commands/",
    )
    response_data = response_get.json()

    assert isinstance(response_data, list)
    assert commands_count + 1 == len(response_data)  # + master command
    for command in response_data:
        assert isinstance(command, dict)
        assert command.get("id") is not None


async def test_get_specific_command(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    get_master_token: str,
) -> None:
    """Test retrieving the command."""
    commands = list()
    for _ in range(random.randint(10, 20)):
        master_response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/commands/",
            json={
                "name": fake_instance.unique.company(),
                "description": fake_instance.text(max_nb_chars=500),
            },
            headers={"Authorization": f"Bearer {get_master_token}"},
        )

        assert master_response_create.status_code == 201

        response_create_data = master_response_create.json()

        assert isinstance(response_create_data, dict)

        commands.append(response_create_data)

    for command in commands:
        command_id = command.get("id")

        assert command_id is not None

        response_get = await httpx_test_client.get(
            url=f"{ORG_PREFIX}/commands/{command_id}/",
        )

        assert response_get.status_code == 200

        response_get_data = response_get.json()

        assert isinstance(response_get_data, dict)
        assert response_get_data.get("id") == command_id
        assert response_get_data.get("created_at") is not None
        assert response_get_data.get("updated_at") is not None


async def test_update_command(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    get_master_token: str,
) -> None:
    """Test updating the command."""
    commands = list()
    for _ in range(random.randint(10, 20)):
        master_response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/commands/",
            json={
                "name": fake_instance.unique.company(),
                "description": fake_instance.text(max_nb_chars=500),
            },
            headers={"Authorization": f"Bearer {get_master_token}"},
        )

        assert master_response_create.status_code == 201

        response_create_data = master_response_create.json()

        assert isinstance(response_create_data, dict)

        commands.append(response_create_data)

    updating_data = {
        "description": fake_instance.text(max_nb_chars=400),
    }
    some_existing_command: dict = random.choice(commands)
    some_command_id = some_existing_command.get("id")

    assert some_command_id is not None

    response_update = await httpx_test_client.put(
        url=f"{ORG_PREFIX}/commands/{some_command_id}/",
        json=updating_data,
    )

    assert response_update.status_code == 401

    master_response_update = await httpx_test_client.put(
        url=f"{ORG_PREFIX}/commands/{some_command_id}/",
        json=updating_data,
        headers={"Authorization": f"Bearer {get_master_token}"},
    )
    assert master_response_update.status_code == 200

    response_update_data = master_response_update.json()

    assert isinstance(response_update_data, dict)
    assert some_command_id == response_update_data.get("id")
    assert some_existing_command.get(
        "description"
    ) != response_update_data.get("description")
    assert updating_data.get("description") == response_update_data.get(
        "description"
    )


async def test_deactivate_activate_command(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    get_master_token: str,
) -> None:
    """Test deactivating the command then activating it."""
    commands = list()
    for _ in range(random.randint(10, 20)):
        master_response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/commands/",
            json={
                "name": fake_instance.unique.company(),
                "description": fake_instance.text(max_nb_chars=500),
            },
            headers={"Authorization": f"Bearer {get_master_token}"},
        )

        assert master_response_create.status_code == 201

        response_create_data = master_response_create.json()

        assert isinstance(response_create_data, dict)

        commands.append(response_create_data)

    some_command: dict = random.choice(commands)
    some_command_id = some_command.get("id")

    assert some_command_id is not None

    resp_deactivate = await httpx_test_client.delete(
        url=f"{ORG_PREFIX}/commands/{some_command_id}/",
    )

    assert resp_deactivate.status_code == 401

    master_resp_deactivate = await httpx_test_client.delete(
        url=f"{ORG_PREFIX}/commands/{some_command_id}/",
        headers={"Authorization": f"Bearer {get_master_token}"},
    )
    assert master_resp_deactivate.status_code == 204

    master_resp_activate = await httpx_test_client.post(
        url=f"{ORG_PREFIX}/commands/{some_command_id}/activate/",
        headers={"Authorization": f"Bearer {get_master_token}"},
    )

    assert master_resp_activate.status_code == 200
