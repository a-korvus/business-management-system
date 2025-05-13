"""Infrastructure interfaces in the 'app_team'."""

import abc
import uuid
from datetime import date, datetime
from decimal import Decimal

from project.app_auth.domain.models import User
from project.app_org.domain.models import Command
from project.app_team.domain.models import (
    CalendarEvent,
    Meeting,
    Task,
    TaskComment,
)


class AbsPartnerRepo(abc.ABC):
    """Interface for implementing User-related operations."""

    @abc.abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get User by ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_command_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> uuid.UUID | None:
        """Get command ID of user by user ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_command_by_id(self, command_id: uuid.UUID) -> Command | None:
        """Get command by ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def user_share_command_id(
        self,
        user_ids: list[uuid.UUID] | set[uuid.UUID],
        target_command_id: uuid.UUID,
    ) -> bool:
        """Check all users in the list belong to the same command."""
        raise NotImplementedError

    @abc.abstractmethod
    async def users_in_seq(
        self,
        user_ids: list[uuid.UUID] | set[uuid.UUID],
    ) -> list[User]:
        """Get users by its IDs."""
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
    async def get_assigned_period(
        self,
        assignee_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[Task]:
        """Get all tasks assigned to a user for a specified period."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_grades_assigned_period(
        self,
        assignee_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[tuple[str, int]]:
        """Get task titles and grades assigned to a user.

        For a specified period.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def get_avg_grade_period(
        self,
        assignee_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal | None:
        """Get average grade of user tasks for a specified period."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_avg_grade_period_command(
        self,
        command_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal | None:
        """Get average grade of command for a specified period."""
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


class AbsCalendarEventRepo(abc.ABC):
    """Interface for implementing model-specific CalendarEvent operations."""

    @abc.abstractmethod
    async def get_by_id(self, c_event_id: uuid.UUID) -> CalendarEvent | None:
        """Get CalendarEvent by its ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id_detail(
        self,
        c_event_id: uuid.UUID,
    ) -> CalendarEvent | None:
        """Get CalendarEvent by its ID. Load all relationships."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all_period(
        self,
        start_date: date,
        end_date: date,
    ) -> list[CalendarEvent]:
        """Get list of CalendarEvent objects for the specified period."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, c_event: CalendarEvent) -> None:
        """Add CalendarEvent object to session."""
        raise NotImplementedError

    @abc.abstractmethod
    async def check_overlap_users(
        self,
        start_time: datetime,
        end_time: datetime,
        user_ids: set[uuid.UUID],
        event_id: uuid.UUID,
    ) -> uuid.UUID | None:
        """Check if existing user events overlap with the new event."""
        raise NotImplementedError


class AbsMeetingRepo(abc.ABC):
    """Interface for implementing model-specific Meeting operations."""

    @abc.abstractmethod
    async def get_by_id(self, meeting_id: uuid.UUID) -> Meeting | None:
        """Get Meeting by its ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_id_detail(self, meeting_id: uuid.UUID) -> Meeting | None:
        """Get Meeting by its ID. Load all relationships."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add(self, meeting: Meeting) -> None:
        """Add Meeting object to session."""
        raise NotImplementedError
