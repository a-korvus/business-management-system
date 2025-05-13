"""Test TaskService from 'app_team'."""

import random
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_org.domain.models import Command
from project.app_team.application.enums import TaskGrade, TaskStatus
from project.app_team.application.schemas import (
    Period,
    TaskCreate,
    TaskUpdate,
)
from project.app_team.application.services.task import TaskService
from project.app_team.domain.models import CalendarEvent, Task
from project.core.log_config import get_logger

logger = get_logger(__name__)
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]


async def test_create_assignment(
    verify_task_service: TaskService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test creating a task."""
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    assignee_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    date_end = datetime.now(timezone.utc) + timedelta(days=2)
    relate_event = CalendarEvent(
        title=fake_instance.text(max_nb_chars=500),
        start_time=datetime.now(timezone.utc) + timedelta(days=1),
        end_time=date_end,
    )
    db_session.add_all([assignee_user, creator_user, relate_event])
    await db_session.commit()

    assert isinstance(creator_user, User)
    assert creator_user.id is not None
    assert isinstance(assignee_user, User)
    assert assignee_user.id is not None
    assert isinstance(relate_event, CalendarEvent)
    assert relate_event.id is not None

    new_task_schema = TaskCreate(
        title=fake_instance.text(max_nb_chars=500),
        due_date=date_end,
        creator_id=creator_user.id,
        assignee_id=assignee_user.id,
        calendar_event_id=relate_event.id,
    )
    new_task = await verify_task_service.create_assignment(new_task_schema)

    assert isinstance(new_task, Task)
    assert new_task.id is not None
    assert new_task.is_active is True
    assert isinstance(new_task.created_at, datetime)
    assert isinstance(new_task.updated_at, datetime)
    assert new_task.description is None
    assert new_task.status == TaskStatus.OPEN
    assert new_task.creator_id == creator_user.id
    assert new_task.assignee_id == assignee_user.id
    assert new_task.calendar_event_id == relate_event.id


async def test_update_task(
    verify_task_service: TaskService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test updating a task."""
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    assignee_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(creator_user)
    db_session.add(assignee_user)
    await db_session.flush([creator_user, assignee_user])

    assert creator_user.id is not None
    assert assignee_user.id is not None

    first_title = fake_instance.text(max_nb_chars=500)
    new_task = Task(
        title=first_title,
        due_date=datetime.now(timezone.utc) + timedelta(days=2),
        creator_id=creator_user.id,
        assignee_id=assignee_user.id,
    )
    db_session.add(new_task)
    await db_session.commit()

    assert new_task.id is not None

    update_schema = TaskUpdate(
        title=fake_instance.text(max_nb_chars=200),
    )
    upd_task = await verify_task_service.update_task(
        task_id=new_task.id,
        data=update_schema,
    )

    assert isinstance(upd_task, Task)
    assert upd_task.id == new_task.id
    assert upd_task.title != first_title
    assert upd_task.title == update_schema.title


async def test_update_task_status(
    verify_task_service: TaskService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test updating a task. Set new status."""
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    assignee_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(creator_user)
    db_session.add(assignee_user)
    await db_session.flush([creator_user, assignee_user])

    assert creator_user.id is not None
    assert assignee_user.id is not None

    new_task = Task(
        title=fake_instance.text(max_nb_chars=500),
        due_date=datetime.now(timezone.utc) + timedelta(days=2),
        creator_id=creator_user.id,
        assignee_id=assignee_user.id,
    )
    db_session.add(new_task)
    await db_session.commit()

    assert new_task.id is not None
    assert new_task.status == TaskStatus.OPEN

    update_schema = TaskUpdate(status="in_progress")  # type: ignore
    upd_task = await verify_task_service.update_task(
        task_id=new_task.id,
        data=update_schema,
    )

    assert isinstance(upd_task, Task)
    assert upd_task.id == new_task.id
    assert upd_task.status == TaskStatus.IN_PROGRESS


async def test_update_task_grade(
    verify_task_service: TaskService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test updating a task. Set new grade."""
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    assignee_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(creator_user)
    db_session.add(assignee_user)
    await db_session.flush([creator_user, assignee_user])

    assert creator_user.id is not None
    assert assignee_user.id is not None

    new_task = Task(
        title=fake_instance.text(max_nb_chars=500),
        due_date=datetime.now(timezone.utc) + timedelta(days=2),
        creator_id=creator_user.id,
        assignee_id=assignee_user.id,
    )
    db_session.add(new_task)
    await db_session.commit()

    assert new_task.id is not None
    assert new_task.grade is None

    update_schema = TaskUpdate(grade=2)
    upd_task = await verify_task_service.update_task(
        task_id=new_task.id,
        data=update_schema,
    )

    assert isinstance(upd_task, Task)
    assert upd_task.id == new_task.id
    assert upd_task.grade == TaskGrade.DONE_DEADLINE


async def test_update_task_event(
    verify_task_service: TaskService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test updating a task. Set related event."""
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    assignee_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    date_end = datetime.now(timezone.utc) + timedelta(days=2)
    relate_event = CalendarEvent(
        title=fake_instance.text(max_nb_chars=500),
        start_time=datetime.now(timezone.utc) + timedelta(days=1),
        end_time=date_end,
    )
    db_session.add_all([assignee_user, creator_user, relate_event])
    await db_session.flush([creator_user, assignee_user, relate_event])

    assert creator_user.id is not None
    assert assignee_user.id is not None
    assert relate_event.id is not None

    new_task = Task(
        title=fake_instance.text(max_nb_chars=500),
        due_date=date_end,
        creator_id=creator_user.id,
        assignee_id=assignee_user.id,
    )
    db_session.add(new_task)
    await db_session.commit()

    assert new_task.id is not None
    assert new_task.calendar_event_id is None

    update_schema = TaskUpdate(calendar_event_id=relate_event.id)
    upd_task = await verify_task_service.update_task(
        task_id=new_task.id,
        data=update_schema,
    )

    assert isinstance(upd_task, Task)
    assert upd_task.id == new_task.id
    assert upd_task.calendar_event_id == relate_event.id


async def test_deactivate_task(
    verify_task_service: TaskService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test deactivating a task."""
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    assignee_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(creator_user)
    db_session.add(assignee_user)
    await db_session.flush([creator_user, assignee_user])

    assert creator_user.id is not None
    assert assignee_user.id is not None

    task = Task(
        title=fake_instance.text(max_nb_chars=500),
        due_date=datetime.now(timezone.utc) + timedelta(days=2),
        creator_id=creator_user.id,
        assignee_id=assignee_user.id,
    )
    db_session.add(task)
    await db_session.commit()

    assert task.id is not None
    assert task.is_active is True

    await verify_task_service.deactivate_task(task.id)

    assert task.is_active is False


async def test_get_assigned_tasks(
    verify_task_service: TaskService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test receiving all existing tasks assigned to a user."""
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    assignee_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(creator_user)
    db_session.add(assignee_user)
    await db_session.flush([creator_user, assignee_user])

    task_count = 0
    for _ in range(3, 10):
        db_session.add(
            Task(
                title=fake_instance.text(max_nb_chars=random.randint(10, 500)),
                description=fake_instance.text(
                    max_nb_chars=random.randint(10, 1000),
                ),
                due_date=datetime.now(timezone.utc)
                + timedelta(days=random.randint(1, 15)),
                creator_id=str(creator_user.id),
                assignee_id=str(assignee_user.id),
            )
        )
        task_count += 1
    await db_session.commit()

    requested_period = Period(
        start=datetime.now(timezone.utc).date() - timedelta(days=1),
        end=datetime.now(timezone.utc).date() + timedelta(days=15),
    )
    assigned_tasks = await verify_task_service.get_assigned_tasks(
        assignee_id=assignee_user.id,
        period=requested_period,
    )

    assert isinstance(assigned_tasks, list)
    assert len(assigned_tasks) == task_count


async def test_get_grades_assigned_tasks(
    verify_task_service: TaskService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test receiving all existing tasks assigned to a user."""
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    assignee_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(creator_user)
    db_session.add(assignee_user)
    await db_session.flush([creator_user, assignee_user])

    task_count = 0
    for _ in range(3, 10):
        db_session.add(
            Task(
                title=fake_instance.text(max_nb_chars=random.randint(10, 500)),
                description=fake_instance.text(
                    max_nb_chars=random.randint(10, 1000),
                ),
                grade=random.choice(TaskGrade.get_values()),
                due_date=datetime.now(timezone.utc)
                + timedelta(days=random.randint(1, 15)),
                creator_id=str(creator_user.id),
                assignee_id=str(assignee_user.id),
            )
        )
        task_count += 1
    await db_session.commit()

    requested_period = Period(
        start=datetime.now(timezone.utc).date() - timedelta(days=1),
        end=datetime.now(timezone.utc).date() + timedelta(days=15),
    )
    assigned_tasks = await verify_task_service.get_grades_assigned_tasks(
        assignee_id=assignee_user.id,
        period=requested_period,
    )

    assert isinstance(assigned_tasks, list)
    assert len(assigned_tasks) == task_count
    for result in assigned_tasks:
        assert isinstance(result, tuple)
        assert result[1] in TaskGrade.get_values()


async def test_get_avg_grade_period(
    verify_task_service: TaskService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test receiving average grade of user tasks for a specified period."""
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    assignee_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(creator_user)
    db_session.add(assignee_user)
    await db_session.flush([creator_user, assignee_user])

    total_grade = Decimal("0")
    task_count = 0
    for _ in range(3, 10):
        grade = random.choice(TaskGrade.get_values())
        db_session.add(
            Task(
                title=fake_instance.text(max_nb_chars=random.randint(10, 500)),
                description=fake_instance.text(
                    max_nb_chars=random.randint(10, 1000),
                ),
                grade=grade,
                due_date=datetime.now(timezone.utc)
                + timedelta(days=random.randint(1, 15)),
                creator_id=str(creator_user.id),
                assignee_id=str(assignee_user.id),
            )
        )
        total_grade += Decimal(grade)
        task_count += 1
    await db_session.commit()

    expected_avg = total_grade / Decimal(task_count)
    expected_avg_round = expected_avg.quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )
    requested_period = Period(
        start=datetime.now(timezone.utc).date() - timedelta(days=1),
        end=datetime.now(timezone.utc).date() + timedelta(days=15),
    )
    avg_grade = await verify_task_service.get_avg_grade_period(
        assignee_id=assignee_user.id,
        period=requested_period,
    )

    assert isinstance(avg_grade, Decimal)
    assert expected_avg_round == avg_grade


async def test_get_avg_grade_period_command(
    verify_task_service: TaskService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test receiving average grade of user command for a specified period."""
    user_1 = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    user_2 = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(user_1)
    db_session.add(user_2)
    await db_session.flush([user_1, user_2])

    command = Command(name=fake_instance.company())
    command.users.append(user_1)
    command.users.append(user_2)
    db_session.add(command)

    total_grade_1 = Decimal("0")
    total_grade_2 = Decimal("0")
    task_count = 0

    for _ in range(3, 10):
        grade_1 = random.choice(TaskGrade.get_values())
        grade_2 = random.choice(TaskGrade.get_values())

        db_session.add(
            Task(
                title=fake_instance.text(max_nb_chars=random.randint(10, 500)),
                description=fake_instance.text(
                    max_nb_chars=random.randint(10, 1000),
                ),
                grade=grade_2,
                due_date=datetime.now(timezone.utc)
                + timedelta(days=random.randint(1, 15)),
                creator_id=str(user_1.id),
                assignee_id=str(user_2.id),
            )
        )
        db_session.add(
            Task(
                title=fake_instance.text(max_nb_chars=random.randint(10, 500)),
                description=fake_instance.text(
                    max_nb_chars=random.randint(10, 1000),
                ),
                grade=grade_1,
                due_date=datetime.now(timezone.utc)
                + timedelta(days=random.randint(1, 15)),
                creator_id=str(user_2.id),
                assignee_id=str(user_1.id),
            )
        )
        total_grade_1 += Decimal(grade_1)
        total_grade_2 += Decimal(grade_2)
        task_count += 1
    await db_session.commit()

    expected_avg_1 = total_grade_1 / Decimal(task_count)
    expected_avg_2 = total_grade_2 / Decimal(task_count)
    common_avg = (expected_avg_1 + expected_avg_2) / Decimal("2")
    common_avg_round = common_avg.quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )

    requested_period = Period(
        start=datetime.now(timezone.utc).date() - timedelta(days=1),
        end=datetime.now(timezone.utc).date() + timedelta(days=15),
    )
    avg_grade = await verify_task_service.get_avg_grade_period_command(
        assignee_id=user_2.id,
        period=requested_period,
    )

    assert isinstance(avg_grade, Decimal)
    assert common_avg_round == avg_grade
