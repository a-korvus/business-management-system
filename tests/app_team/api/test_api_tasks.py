"""Test API routs for 'tasks' router."""

from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_team.application.enums import TaskStatus
from project.app_team.domain.models import Task
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]

TEAM_PREFIX = settings.PREFIX_TEAM


async def test_create_task(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test creating a new task."""
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

    future_date: datetime = datetime.now(timezone.utc) + timedelta(days=2)
    fake_task_data = {
        "title": fake_instance.text(max_nb_chars=500),
        "due_date": future_date.isoformat(),
        "creator_id": str(creator_user.id),
        "assignee_id": str(assignee_user.id),
    }

    response: Response = await httpx_test_client.post(
        url=f"{TEAM_PREFIX}/tasks/",
        json=fake_task_data,
    )

    assert response.status_code == 201

    new_task_data = response.json()

    assert isinstance(new_task_data, dict)
    assert new_task_data.get("id") is not None
    assert new_task_data.get("title") == fake_task_data["title"]
    assert new_task_data.get("description") is None
    assert new_task_data.get("status") == TaskStatus.OPEN.value
    assert new_task_data.get("grade") is None
    assert new_task_data.get("is_active") is True
    assert isinstance(new_task_data.get("due_date"), str)
    assert isinstance(new_task_data.get("created_at"), str)
    assert isinstance(new_task_data.get("updated_at"), str)
    assert new_task_data.get("creator_id") == fake_task_data["creator_id"]
    assert new_task_data.get("assignee_id") == fake_task_data["assignee_id"]


async def test_update_task(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test updating an existing task."""
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

    new_task = Task(
        title=fake_instance.text(max_nb_chars=100),
        description=fake_instance.text(max_nb_chars=200),
        due_date=datetime.now(timezone.utc) + timedelta(days=2),
        creator_id=str(creator_user.id),
        assignee_id=str(assignee_user.id),
    )
    db_session.add(new_task)
    await db_session.commit()

    upd_task_data = {
        "title": fake_instance.text(max_nb_chars=50),
        "grade": 1,
    }
    response: Response = await httpx_test_client.patch(
        url=f"{TEAM_PREFIX}/tasks/{new_task.id}/",
        json=upd_task_data,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, dict)
    assert response_data.get("grade") == upd_task_data["grade"]
    assert response_data.get("title") == upd_task_data["title"]


async def test_deactivate_task(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test deactivating an existing task."""
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

    new_task = Task(
        title=fake_instance.text(max_nb_chars=100),
        description=fake_instance.text(max_nb_chars=200),
        due_date=datetime.now(timezone.utc) + timedelta(days=2),
        creator_id=str(creator_user.id),
        assignee_id=str(assignee_user.id),
    )
    db_session.add(new_task)
    await db_session.commit()

    response: Response = await httpx_test_client.delete(
        url=f"{TEAM_PREFIX}/tasks/{new_task.id}/",
    )

    assert response.status_code == 204


async def test_create_comment(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test creating a comment to an existing task."""
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

    new_task = Task(
        title=fake_instance.text(max_nb_chars=100),
        description=fake_instance.text(max_nb_chars=200),
        due_date=datetime.now(timezone.utc) + timedelta(days=2),
        creator_id=str(creator_user.id),
        assignee_id=str(assignee_user.id),
    )
    db_session.add(new_task)
    await db_session.commit()

    new_comment_data = {
        "text": fake_instance.text(max_nb_chars=200),
        "task_id": str(new_task.id),
        "commentator_id": str(assignee_user.id),
    }

    response: Response = await httpx_test_client.post(
        url=f"{TEAM_PREFIX}/tasks/comments/",
        json=new_comment_data,
    )

    assert response.status_code == 201

    response_data = response.json()

    assert isinstance(response_data, dict)
    assert response_data.get("id") is not None
    assert response_data.get("is_active") is True
    assert isinstance(response_data.get("created_at"), str)
    assert isinstance(response_data.get("updated_at"), str)
    assert response_data.get("task_id") == str(new_task.id)
    assert response_data.get("commentator_id") == str(assignee_user.id)
    assert response_data.get("parent_comment_id") is None
