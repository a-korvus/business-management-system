"""Test API routs for 'meetings' router."""

import random
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_org.domain.models import Command
from project.app_team.application.services.meeting import MeetingService
from project.app_team.domain.models import Meeting
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]

TEAM_PREFIX = settings.PREFIX_TEAM


async def test_create_meeting(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test creating a new meeting."""
    command = Command(name=fake_instance.unique.company())
    db_session.add(command)
    await db_session.flush([command])

    users_ids = []
    for _ in range(random.randint(3, 7)):
        user = User(
            email=fake_instance.unique.email(),
            plain_password=fake_instance.password(),
            hasher=get_password_hasher(),
            command_id=command.id,
        )
        db_session.add(user)
        await db_session.flush([user])
        users_ids.append(str(user.id))
    await db_session.commit()

    meeting_start = datetime.now(timezone.utc) + timedelta(days=2)
    meeting_end = meeting_start + timedelta(hours=2)
    fake_meeting_data = {
        "topic": fake_instance.text(max_nb_chars=500),
        "start_time": meeting_start.isoformat(),
        "end_time": meeting_end.isoformat(),
        "creator_id": users_ids[0],
        "command_id": str(command.id),
        "members_ids": users_ids,
    }

    response: Response = await httpx_test_client.post(
        url=f"{TEAM_PREFIX}/meetings/",
        json=fake_meeting_data,
    )

    assert response.status_code == 201

    new_meeting_data = response.json()

    assert isinstance(new_meeting_data, dict)
    assert new_meeting_data.get("id") is not None
    assert new_meeting_data.get("calendar_event_id") is not None


async def test_update_meeting(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test updating a meeting."""
    command = Command(name=fake_instance.unique.company())
    db_session.add(command)
    await db_session.flush([command])

    users_ids = []
    for _ in range(random.randint(3, 7)):
        user = User(
            email=fake_instance.unique.email(),
            plain_password=fake_instance.password(),
            hasher=get_password_hasher(),
            command_id=command.id,
        )
        db_session.add(user)
        await db_session.flush([user])
        users_ids.append(str(user.id))
    await db_session.commit()

    meeting_start = datetime.now(timezone.utc) + timedelta(days=2)
    meeting_end = meeting_start + timedelta(hours=2)
    fake_meeting_data = {
        "topic": fake_instance.text(max_nb_chars=500),
        "start_time": meeting_start.isoformat(),
        "end_time": meeting_end.isoformat(),
        "creator_id": users_ids[0],
        "command_id": str(command.id),
        "members_ids": users_ids,
    }

    response_create: Response = await httpx_test_client.post(
        url=f"{TEAM_PREFIX}/meetings/",
        json=fake_meeting_data,
    )

    assert response_create.status_code == 201

    new_meeting_data = response_create.json()

    assert isinstance(new_meeting_data, dict)
    assert new_meeting_data.get("id") is not None
    assert new_meeting_data.get("calendar_event_id") is not None
    assert new_meeting_data.get("status") == "planned"
    assert new_meeting_data.get("description") is None

    upd_data = {
        "status": "completed",
        "description": fake_instance.text(max_nb_chars=500),
    }

    response_update: Response = await httpx_test_client.patch(
        url=f"{TEAM_PREFIX}/meetings/{new_meeting_data.get("id")}/",
        json=upd_data,
    )

    assert response_update.status_code == 200

    upd_meeting_data = response_update.json()

    assert isinstance(upd_meeting_data, dict)
    assert upd_meeting_data.get("id") == new_meeting_data.get("id")
    assert upd_meeting_data.get("status") == "completed"
    assert upd_meeting_data.get("description") == upd_data.get("description")


async def test_deactivate_meeting(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test deactivating a meeting."""
    command = Command(name=fake_instance.unique.company())
    db_session.add(command)
    await db_session.flush([command])

    users_ids = []
    for _ in range(random.randint(3, 7)):
        user = User(
            email=fake_instance.unique.email(),
            plain_password=fake_instance.password(),
            hasher=get_password_hasher(),
            command_id=command.id,
        )
        db_session.add(user)
        await db_session.flush([user])
        users_ids.append(str(user.id))
    await db_session.commit()

    meeting_start = datetime.now(timezone.utc) + timedelta(days=2)
    meeting_end = meeting_start + timedelta(hours=2)
    fake_meeting_data = {
        "topic": fake_instance.text(max_nb_chars=500),
        "start_time": meeting_start.isoformat(),
        "end_time": meeting_end.isoformat(),
        "creator_id": users_ids[0],
        "command_id": str(command.id),
        "members_ids": users_ids,
    }

    response_create: Response = await httpx_test_client.post(
        url=f"{TEAM_PREFIX}/meetings/",
        json=fake_meeting_data,
    )

    assert response_create.status_code == 201

    new_meeting_data = response_create.json()

    assert isinstance(new_meeting_data, dict)
    assert new_meeting_data.get("id") is not None

    response_deactivate: Response = await httpx_test_client.delete(
        url=f"{TEAM_PREFIX}/meetings/{new_meeting_data.get("id")}/",
    )

    assert response_deactivate.status_code == 204


async def test_include_users(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
    verify_meeting_service: MeetingService,
) -> None:
    """Test adding new users to the meeting."""
    command = Command(name=fake_instance.unique.company())
    db_session.add(command)
    await db_session.flush([command])

    users_ids = []
    for _ in range(random.randint(3, 7)):
        user = User(
            email=fake_instance.unique.email(),
            plain_password=fake_instance.password(),
            hasher=get_password_hasher(),
            command_id=command.id,
        )
        db_session.add(user)
        await db_session.flush([user])
        users_ids.append(str(user.id))
    await db_session.commit()

    meeting_start = datetime.now(timezone.utc) + timedelta(days=2)
    meeting_end = meeting_start + timedelta(hours=2)
    fake_meeting_data = {
        "topic": fake_instance.text(max_nb_chars=500),
        "start_time": meeting_start.isoformat(),
        "end_time": meeting_end.isoformat(),
        "creator_id": users_ids[0],
        "command_id": str(command.id),
        "members_ids": users_ids,
    }

    response_create: Response = await httpx_test_client.post(
        url=f"{TEAM_PREFIX}/meetings/",
        json=fake_meeting_data,
    )

    assert response_create.status_code == 201

    new_meeting_data = response_create.json()

    assert isinstance(new_meeting_data, dict)
    assert new_meeting_data.get("id") is not None

    new_users_ids = []
    for _ in range(random.randint(2, 4)):
        user = User(
            email=fake_instance.unique.email(),
            plain_password=fake_instance.password(),
            hasher=get_password_hasher(),
            command_id=command.id,
        )
        db_session.add(user)
        await db_session.flush([user])
        new_users_ids.append(str(user.id))
    await db_session.commit()

    response_update: Response = await httpx_test_client.patch(
        url=f"{TEAM_PREFIX}/meetings/{new_meeting_data.get("id")}/include/",
        json=new_users_ids,
    )
    total_ids = len(users_ids) + len(new_users_ids)

    assert response_update.status_code == 200

    upd_meeting_data = response_update.json()

    assert isinstance(upd_meeting_data, dict)
    assert upd_meeting_data.get("id") == new_meeting_data.get("id")

    meeting_detail = await verify_meeting_service.get_by_id_detail(
        meeting_id=uuid.UUID(upd_meeting_data.get("id")),
    )

    assert isinstance(meeting_detail, Meeting)
    assert total_ids == len(meeting_detail.members)
    assert total_ids == len(meeting_detail.calendar_event.users)
