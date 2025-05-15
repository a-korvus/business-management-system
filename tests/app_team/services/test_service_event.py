"""Test CalendarEvent from 'app_team'."""

import random
from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_team.application.enums import EventType
from project.app_team.application.schemas import CalendarEventCreate, Period
from project.app_team.application.services.calendar_events import (
    CalendarEventService,
)
from project.app_team.domain.exceptions import OverlapError
from project.app_team.domain.models import CalendarEvent
from project.core.log_config import get_logger

logger = get_logger(__name__)
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]


async def test_create_event(
    verify_event_service: CalendarEventService,
    fake_instance: Faker,
) -> None:
    """Test creating a calendar event."""
    event_start = datetime.now(timezone.utc) + timedelta(days=2)
    event_end = event_start + timedelta(hours=2)
    event_schema = CalendarEventCreate(
        title=fake_instance.text(max_nb_chars=500),
        start_time=event_start,
        end_time=event_end,
    )

    new_event = await verify_event_service.create_event(event_schema)

    assert isinstance(new_event, CalendarEvent)
    assert new_event.id is not None
    assert new_event.start_time == event_start
    assert new_event.end_time == event_end
    assert new_event.event_type == EventType.GENERAL
    assert new_event.all_day is False


async def test_get_event_by_id(
    verify_event_service: CalendarEventService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test receiving a calendar event."""
    event_start = datetime.now(timezone.utc) + timedelta(days=2)
    event_end = event_start + timedelta(hours=2)
    new_event = CalendarEvent(
        title=fake_instance.text(max_nb_chars=500),
        start_time=event_start,
        end_time=event_end,
    )
    db_session.add(new_event)
    await db_session.commit()

    assert isinstance(new_event, CalendarEvent)
    assert new_event.id is not None

    receiving_event = await verify_event_service.get_by_id(new_event.id)

    assert isinstance(receiving_event, CalendarEvent)
    assert receiving_event.id == new_event.id


async def test_list_for_period(
    verify_event_service: CalendarEventService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test receiving events for the specified period."""
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

    period = Period(
        start=dt_point.date() + timedelta(days=1),
        end=dt_point.date() + timedelta(days=6),
    )
    filtered_events = await verify_event_service.list_for_period(period)

    assert isinstance(filtered_events, list)
    assert in_period == len(filtered_events)


async def test_include_user(
    verify_event_service: CalendarEventService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test addition a user to an event."""
    user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(user)

    event_start = datetime.now(timezone.utc) + timedelta(days=2)
    event_end = event_start + timedelta(hours=2)
    new_event = CalendarEvent(
        title=fake_instance.text(max_nb_chars=500),
        start_time=event_start,
        end_time=event_end,
    )
    db_session.add(new_event)
    await db_session.commit()

    event = await verify_event_service.include_user(
        user_id=user.id,
        event_id=new_event.id,
    )

    assert isinstance(event, CalendarEvent)
    assert user in event.users

    another_event = CalendarEvent(
        title=fake_instance.text(max_nb_chars=500),
        start_time=event_start - timedelta(hours=1),
        end_time=event_end,
    )
    db_session.add(another_event)
    await db_session.commit()

    assert another_event.id is not None
    with pytest.raises(OverlapError):
        await verify_event_service.include_user(
            user_id=user.id,
            event_id=another_event.id,
        )
