"""Repository interfaces in the 'app_team' app."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from project.app_auth.domain.models import User
from project.app_team.application.interfaces import (
    AbsPartnerRepo,
    AbsTaskCommentRepo,
    AbsTaskRepo,
)
from project.app_team.domain.models import Task, TaskComment


class SAPartnerRepo(AbsPartnerRepo):
    """Implementation of User-related actions."""

    def __init__(self, session: AsyncSession | None) -> None:
        """Initialize a Partner Repository."""
        if session is None:
            raise ValueError(f"{self.__class__.__name__} get an empty session")

        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get User by ID."""
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


class SATaskRepo(AbsTaskRepo):
    """Implementation of tasks repository using sqlalchemy."""

    def __init__(self, session: AsyncSession | None) -> None:
        """Initialize a Task Repository."""
        if session is None:
            raise ValueError(f"{self.__class__.__name__} get an empty session")

        self._session = session

    async def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        """Get Task by its ID."""
        result = await self._session.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_comments(self, task_id: uuid.UUID) -> Task | None:
        """Get Task by its ID with all related comments."""
        result = await self._session.execute(
            select(Task)
            .options(selectinload(Task.comments))
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def add(self, task: Task) -> None:
        """Add a new Task object to session."""
        self._session.add(task)


class SATaskCommentRepo(AbsTaskCommentRepo):
    """Implementation of task commens repository using sqlalchemy."""

    def __init__(self, session: AsyncSession | None) -> None:
        """Initialize a TaskComment Repository."""
        if session is None:
            raise ValueError(f"{self.__class__.__name__} get an empty session")

        self._session = session

    async def get_by_id(self, taskcomment_id: uuid.UUID) -> TaskComment | None:
        """Get TaskComment by its ID."""
        result = await self._session.execute(
            select(TaskComment).where(TaskComment.id == taskcomment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_children(
        self,
        taskcomment_id: uuid.UUID,
    ) -> TaskComment | None:
        """Get TaskComment by its ID with all child comments."""
        result = await self._session.execute(
            select(TaskComment)
            .options(selectinload(TaskComment.child_comments))
            .where(TaskComment.id == taskcomment_id)
        )
        return result.scalar_one_or_none()

    async def add(self, taskcomment: TaskComment) -> None:
        """Add a new TaskComment object to session."""
        self._session.add(taskcomment)
