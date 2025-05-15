"""Test TaskCommentService from 'app_team'."""

from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_team.application.schemas import (
    TaskCommentCreate,
    TaskCommentUpdate,
)
from project.app_team.application.services.task_comment import (
    TaskCommentService,
)
from project.app_team.domain.models import Task, TaskComment

pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]


async def test_create_comment(
    verify_taskcomment_service: TaskCommentService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test creating a comment."""
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

    new_comment_schema = TaskCommentCreate(
        task_id=new_task.id,
        text=fake_instance.text(max_nb_chars=5000),
        commentator_id=assignee_user.id,
    )

    new_comment = await verify_taskcomment_service.create_comment(
        data=new_comment_schema,
    )

    assert isinstance(new_comment, TaskComment)
    assert new_comment.id is not None
    assert new_comment.task_id == new_task.id
    assert new_comment.text is not None
    assert new_comment.parent_comment_id is None
    assert new_comment.commentator_id == assignee_user.id


async def test_update_comment(
    verify_taskcomment_service: TaskCommentService,
    fake_instance: Faker,
    db_session: AsyncSession,
) -> None:
    """Test updating comment."""
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
    await db_session.flush([new_task])

    assert new_task.id is not None

    first_text = fake_instance.text(max_nb_chars=5000)
    new_comment = TaskComment(
        task_id=new_task.id,
        text=first_text,
        commentator_id=assignee_user.id,
    )
    db_session.add(new_comment)
    await db_session.commit()

    assert new_comment.id is not None

    upd_data = TaskCommentUpdate(text=fake_instance.text(max_nb_chars=500))
    upd_comment = await verify_taskcomment_service.update_comment(
        comment_id=new_comment.id,
        data=upd_data,
    )

    assert isinstance(upd_comment, TaskComment)
    assert upd_comment.id is not None
    assert upd_comment.text != first_text
    assert upd_comment.text == upd_data.text
