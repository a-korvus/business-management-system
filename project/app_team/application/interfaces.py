"""Infrastructure interfaces in the 'app_team'."""

import abc
import uuid

from project.app_auth.domain.models import User
from project.app_team.domain.models import Task, TaskComment


class AbsPartnerRepo(abc.ABC):
    """Interface for implementing User-related operations."""

    @abc.abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get User by ID."""
        raise NotImplementedError


class AbsTaskRepo(abc.ABC):
    """Interface for implementing model-specific Task operations."""

    @abc.abstractmethod
    async def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        """Get Task by its ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id_comments(self, task_id: uuid.UUID) -> Task | None:
        """Get Task by its ID with all related comments."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, task: Task) -> None:
        """Add Task object to session."""
        raise NotImplementedError


class AbsTaskCommentRepo(abc.ABC):
    """Interface for implementing model-specific TaskComment operations."""

    @abc.abstractmethod
    async def get_by_id(self, taskcomment_id: uuid.UUID) -> TaskComment | None:
        """Get TaskComment by its ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id_children(
        self,
        taskcomment_id: uuid.UUID,
    ) -> TaskComment | None:
        """Get TaskComment by its ID with all child comments."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, taskcomment: TaskComment) -> None:
        """Add TaskComment object to session."""
        raise NotImplementedError
