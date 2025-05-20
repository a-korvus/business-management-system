"""Test MeetingService from 'app_team'."""

import random
from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_org.domain.models import Command
from project.app_team.application.enums import EventType, MeetingStatus
from project.app_team.application.schemas import MeetingCreate, MeetingUpdate
from project.app_team.application.services.meeting import MeetingService
from project.app_team.domain.models import Meeting
from project.core.log_config import get_logger

logger = get_logger(__name__)
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]


async def test_create(
    verify_meeting_service: MeetingService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test creating a meeting."""
    # создать команду
    command = Command(name=fake_instance.unique.company())
    db_session.add(command)
    await db_session.flush([command])

    # создать несколько пользователей, привязать к команде, собрать их IDs
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
        users_ids.append(user.id)
    await db_session.commit()

    # создать встречу; здесь же создается calendar event
    meeting_start = datetime.now(timezone.utc) + timedelta(days=2)
    meeting_end = meeting_start + timedelta(hours=2)
    meeting_schema = MeetingCreate(
        topic=fake_instance.text(max_nb_chars=500),
        start_time=meeting_start,
        end_time=meeting_end,
        creator_id=users_ids[0],
        command_id=command.id,
        members_ids=users_ids,
    )
    meeting = await verify_meeting_service.create(meeting_schema)

    # проверки
    assert isinstance(meeting, Meeting)
    assert meeting.id is not None
    assert meeting_start == meeting.start_time
    assert meeting_end == meeting.end_time
    assert MeetingStatus.PLANNED == meeting.status
    assert len(users_ids) == len(meeting.members)
    assert meeting.calendar_event.id is not None
    assert len(users_ids) == len(meeting.calendar_event.users)
    assert meeting.command_id == command.id
    assert meeting.start_time == meeting.calendar_event.start_time
    assert meeting.end_time == meeting.calendar_event.end_time
    assert EventType.MEETING == meeting.calendar_event.event_type


async def test_update(
    verify_meeting_service: MeetingService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test updating a meeting."""
    # создать команду
    command = Command(name=fake_instance.unique.company())
    db_session.add(command)
    await db_session.flush([command])

    # создать несколько пользователей, привязать к команде, собрать их IDs
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
        users_ids.append(user.id)
    await db_session.commit()

    # создать встречу; здесь же создается calendar event
    meeting_start = datetime.now(timezone.utc) + timedelta(days=2)
    meeting_end = meeting_start + timedelta(hours=2)
    meeting_schema = MeetingCreate(
        topic=fake_instance.text(max_nb_chars=500),
        start_time=meeting_start,
        end_time=meeting_end,
        creator_id=users_ids[0],
        command_id=command.id,
        members_ids=users_ids,
    )
    meeting = await verify_meeting_service.create(meeting_schema)

    assert isinstance(meeting, Meeting)
    assert meeting.id is not None
    assert meeting.description is None
    assert MeetingStatus.PLANNED == meeting.status

    upd_data = MeetingUpdate(
        description=fake_instance.text(max_nb_chars=500),
        status=MeetingStatus.COMPLETED,
    )
    upd_meeting = await verify_meeting_service.update(
        meeting_id=meeting.id,
        data=upd_data,
    )

    assert isinstance(upd_meeting, Meeting)
    assert meeting.id == upd_meeting.id
    assert meeting_schema.description != upd_meeting.description
    assert MeetingStatus.PLANNED != upd_meeting.status
    assert upd_data.description == upd_meeting.description
    assert upd_data.status == upd_meeting.status


async def test_deactivate(
    verify_meeting_service: MeetingService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test deactivating a meeting."""
    # создать команду
    command = Command(name=fake_instance.unique.company())
    db_session.add(command)
    await db_session.flush([command])

    # создать несколько пользователей, привязать к команде, собрать их IDs
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
        users_ids.append(user.id)
    await db_session.commit()

    # создать встречу; здесь же создается calendar event
    meeting_start = datetime.now(timezone.utc) + timedelta(days=2)
    meeting_end = meeting_start + timedelta(hours=2)
    meeting_schema = MeetingCreate(
        topic=fake_instance.text(max_nb_chars=500),
        start_time=meeting_start,
        end_time=meeting_end,
        creator_id=users_ids[0],
        command_id=command.id,
        members_ids=users_ids,
    )
    meeting = await verify_meeting_service.create(meeting_schema)

    assert isinstance(meeting, Meeting)
    assert meeting.id is not None
    assert meeting.is_active is True

    await verify_meeting_service.deactivate(meeting.id)

    assert meeting.is_active is False


async def test_include_users(
    verify_meeting_service: MeetingService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test adding users to a meeting."""
    # создать команду
    command = Command(name=fake_instance.unique.company())
    db_session.add(command)
    await db_session.flush([command])

    # создать несколько пользователей, привязать к команде, собрать их IDs
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
        users_ids.append(user.id)
    await db_session.commit()

    # создать встречу; здесь же создается calendar event
    meeting_start = datetime.now(timezone.utc) + timedelta(days=2)
    meeting_end = meeting_start + timedelta(hours=2)
    meeting_schema = MeetingCreate(
        topic=fake_instance.text(max_nb_chars=500),
        start_time=meeting_start,
        end_time=meeting_end,
        creator_id=users_ids[0],
        command_id=command.id,
        members_ids=users_ids,
    )
    meeting = await verify_meeting_service.create(meeting_schema)

    assert isinstance(meeting, Meeting)
    assert meeting.id is not None

    # создать новых пользователей
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
        new_users_ids.append(user.id)
    await db_session.commit()

    upd_meeting = await verify_meeting_service.include_users(
        meeting_id=meeting.id,
        user_ids=new_users_ids,
    )
    total_ids = len(users_ids) + len(new_users_ids)
    assert upd_meeting.id == meeting.id
    assert total_ids == len(upd_meeting.members)
    assert total_ids == len(upd_meeting.calendar_event.users)
