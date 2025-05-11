"""Test TaskService from 'app_team'."""

from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_team.application.enums import TaskGrade, TaskStatus
from project.app_team.application.schemas import TaskCreate, TaskUpdate
from project.app_team.application.services.task import TaskService
from project.app_team.domain.models import Task

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
    db_session.add(creator_user)
    db_session.add(assignee_user)
    await db_session.commit()

    assert isinstance(creator_user, User)
    assert creator_user.id is not None
    assert isinstance(assignee_user, User)
    assert assignee_user.id is not None

    new_task_schema = TaskCreate(
        title=fake_instance.text(max_nb_chars=500),
        due_date=datetime.now(timezone.utc) + timedelta(days=2),
        creator_id=creator_user.id,
        assignee_id=assignee_user.id,
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
