"""Test API routs for 'tasks' router."""

import random
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import pytest
from faker import Faker
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_org.domain.models import Command
from project.app_team.application.enums import TaskGrade, TaskStatus
from project.app_team.domain.models import Task
from project.config import settings
from project.core.log_config import get_logger
from tests.helpers import get_auth_token

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


async def test_get_assigned_tasks(
    authenticated_user: dict[str, Any],
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test receiving all existing tasks assigned to a user."""
    token = authenticated_user["token"]
    assignee_user_data = authenticated_user["user"]
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(creator_user)
    await db_session.flush([creator_user])

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
                assignee_id=assignee_user_data["id"],
            )
        )
        task_count += 1
    await db_session.commit()

    date_start = datetime.now(timezone.utc).date()
    date_end = datetime.now(timezone.utc).date() + timedelta(days=15)
    query = f"?start={date_start.isoformat()}&end={date_end.isoformat()}"

    response: Response = await httpx_test_client.get(
        url=f"{TEAM_PREFIX}/tasks/me/{query}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, list)
    assert len(response_data) == task_count


async def test_get_grades_assigned_tasks(
    authenticated_user: dict[str, Any],
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test receiving all existing tasks assigned to a user."""
    token = authenticated_user["token"]
    assignee_user_data = authenticated_user["user"]
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(creator_user)
    await db_session.flush([creator_user])

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
                assignee_id=assignee_user_data["id"],
            )
        )
        task_count += 1
    await db_session.commit()

    date_start = datetime.now(timezone.utc).date()
    date_end = datetime.now(timezone.utc).date() + timedelta(days=15)
    query = f"?start={date_start.isoformat()}&end={date_end.isoformat()}"

    response: Response = await httpx_test_client.get(
        url=f"{TEAM_PREFIX}/tasks/me/grades/{query}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, list)
    assert len(response_data) == task_count
    for result in response_data:
        assert isinstance(result, list)
        assert result[1] in TaskGrade.get_values()


async def test_get_avg_grade_period(
    authenticated_user: dict[str, Any],
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test receiving average user grade for a specified period."""
    token = authenticated_user["token"]
    assignee_user_data = authenticated_user["user"]
    creator_user = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
    )
    db_session.add(creator_user)
    await db_session.flush([creator_user])

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
                assignee_id=assignee_user_data["id"],
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

    date_start = datetime.now(timezone.utc).date()
    date_end = datetime.now(timezone.utc).date() + timedelta(days=15)
    query = f"?start={date_start.isoformat()}&end={date_end.isoformat()}"

    response: Response = await httpx_test_client.get(
        url=f"{TEAM_PREFIX}/tasks/me/grades/avg/{query}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, dict)
    assert "avg_grade" in response_data
    assert isinstance(response_data.get("avg_grade"), str)
    assert response_data.get("avg_grade") == str(expected_avg_round)


async def test_get_avg_grade_period_command(
    httpx_test_client: AsyncClient,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test receiving average user command grade for a specified period."""
    # создаем команду
    command = Command(name=fake_instance.company())
    db_session.add(command)
    await db_session.flush([command])

    # создаем пользователей и привязываем первого пользователя к команде
    user_1_email = fake_instance.unique.email()
    user_1_password = fake_instance.password()
    user_1 = User(
        email=user_1_email,
        plain_password=user_1_password,
        hasher=get_password_hasher(),
        command_id=command.id,
    )
    user_2 = User(
        email=fake_instance.unique.email(),
        plain_password=fake_instance.password(),
        hasher=get_password_hasher(),
        command_id=command.id,
    )
    db_session.add(user_1)
    db_session.add(user_2)
    await db_session.flush([user_1, user_2])

    # создаем задачи с оценками для разных пользователей
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

    # расчитываем общую среднюю оценку из назначенных оценок
    expected_avg_1 = total_grade_1 / Decimal(task_count)
    expected_avg_2 = total_grade_2 / Decimal(task_count)
    common_avg = (expected_avg_1 + expected_avg_2) / Decimal("2")
    common_avg_round = common_avg.quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )

    # формируем ОСНОВНОЙ ЗАПРОС на тестируемый эндпоинт
    date_start = datetime.now(timezone.utc).date()
    date_end = datetime.now(timezone.utc).date() + timedelta(days=15)
    query = f"?start={date_start.isoformat()}&end={date_end.isoformat()}"

    user_1_token: str = await get_auth_token(
        httpx_client=httpx_test_client,
        email=user_1_email,
        password=user_1_password,
    )

    response: Response = await httpx_test_client.get(
        url=f"{TEAM_PREFIX}/tasks/me/grades/avg/command/{query}",
        headers={"Authorization": f"Bearer {user_1_token}"},
    )

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, dict)
    assert "command_avg_grade" in response_data
    assert isinstance(response_data.get("command_avg_grade"), str)
    assert response_data.get("command_avg_grade") == str(common_avg_round)
