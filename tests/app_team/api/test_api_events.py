"""Test API routs for 'events' router."""

import random
from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_team.domain.models import CalendarEvent
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]

TEAM_PREFIX = settings.PREFIX_TEAM


async def test_create_event(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
) -> None:
    """Test creating a calendar event."""
    dt_point = datetime.now(timezone.utc)
    event_start = dt_point + timedelta(days=random.randint(1, 5))
    event_end = event_start + timedelta(hours=random.randint(1, 3))
    fake_event_data = {
        "title": fake_instance.text(max_nb_chars=500),
        "start_time": event_start.isoformat(),
        "end_time": event_end.isoformat(),
    }

    response: Response = await httpx_test_client.post(
        url=f"{TEAM_PREFIX}/events/",
        json=fake_event_data,
    )

    assert response.status_code == 201

    new_event_data = response.json()

    assert isinstance(new_event_data, dict)
    assert new_event_data.get("id") is not None


async def test_get_events_period(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test receiving calendar events for a period."""
    in_period = 0
    dt_point = datetime.now(timezone.utc)
    for _ in range(random.randint(10, 20)):
        event_start = dt_point + timedelta(days=random.randint(1, 5))
        event_end = event_start + timedelta(hours=random.randint(1, 3))
        new_event = CalendarEvent(
            title=fake_instance.text(max_nb_chars=500),
            start_time=event_start,
            end_time=event_end,
        )
        db_session.add(new_event)
        in_period += 1

    for _ in range(random.randint(3, 7)):
        event_start = datetime.now(timezone.utc) + timedelta(
            days=random.randint(7, 10),
        )
        event_end = event_start + timedelta(hours=random.randint(1, 3))
        new_event = CalendarEvent(
            title=fake_instance.text(max_nb_chars=500),
            start_time=event_start,
            end_time=event_end,
        )
        db_session.add(new_event)

    await db_session.commit()

    start_period: str = (dt_point.date() + timedelta(days=1)).isoformat()
    end_period: str = (dt_point.date() + timedelta(days=6)).isoformat()
    query = f"?start={start_period}&end={end_period}"

    response: Response = await httpx_test_client.get(
        url=f"{TEAM_PREFIX}/events/{query}",
    )

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, list)
    assert in_period == len(response_data)


async def test_include_user(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test including users to the calendar event."""
    user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(user)

    event_start = datetime.now(timezone.utc) + timedelta(days=2)
    event_end = event_start + timedelta(hours=2)
    event = CalendarEvent(
        title=fake_instance.text(max_nb_chars=500),
        start_time=event_start,
        end_time=event_end,
    )
    db_session.add(event)
    await db_session.commit()

    payload = {"user_id": str(user.id), "event_id": str(event.id)}
    response: Response = await httpx_test_client.patch(
        url=f"{TEAM_PREFIX}/events/",
        json=payload,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, dict)
    assert response_data.get("id") == str(event.id)
