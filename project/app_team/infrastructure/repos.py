"""Repository interfaces in the 'app_team' app."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import String, and_, case, cast, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql.expression import ColumnElement

from project.app_auth.domain.models import User
from project.app_org.domain.models import Command
from project.app_team.application.enums import TaskGrade
from project.app_team.application.interfaces import (
    AbsCalendarEventRepo,
    AbsMeetingRepo,
    AbsPartnerRepo,
    AbsTaskCommentRepo,
    AbsTaskRepo,
)
from project.app_team.domain.models import (
    CalendarEvent,
    Meeting,
    Task,
    TaskComment,
    users_calendar_events_table,
)
from project.core.db.utils import load_all_relationships


class SAPartnerRepo(AbsPartnerRepo):
    """Implementation of User-related actions."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize a Partner Repository."""
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get User by ID."""
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_command_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> uuid.UUID | None:
        """Get command ID of user by user ID."""
        result = await self._session.execute(
            select(User.command_id).where(User.id == user_id)
        )
        command_id = result.scalar_one_or_none()
        if not command_id:
            return None
        return command_id

    async def get_command_by_id(self, command_id: uuid.UUID) -> Command | None:
        """Get command by ID."""
        result = await self._session.execute(
            select(Command).where(Command.id == command_id)
        )
        return result.scalar_one_or_none()

    async def user_share_command_id(
        self,
        user_ids: list[uuid.UUID] | set[uuid.UUID],
        target_command_id: uuid.UUID,
    ) -> bool:
        """Check all users in the list belong to the same command."""
        if not user_ids:
            return False

        if isinstance(user_ids, list):
            uniq_user_ids = set(user_ids)
        else:
            uniq_user_ids = user_ids
        if len(uniq_user_ids) == 0:
            return False

        stmt = select(func.count(User.id)).where(
            User.id.in_(uniq_user_ids),
            User.command_id == target_command_id,
        )
        result = await self._session.execute(stmt)
        count_matching_users = result.scalar_one_or_none()

        if count_matching_users is None:
            return False

        return count_matching_users == len(uniq_user_ids)

    async def users_in_seq(
        self,
        user_ids: list[uuid.UUID] | set[uuid.UUID],
    ) -> list[User]:
        """Get users by its IDs."""
        if isinstance(user_ids, list):
            user_ids = set(user_ids)

        if not user_ids:
            raise ValueError("Got an empty ids list.")

        result = await self._session.execute(
            select(User).where(User.id.in_(user_ids))
        )
        return list(result.unique().scalars().all())


class SATaskRepo(AbsTaskRepo):
    """Implementation of tasks repository using sqlalchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize a Task Repository."""
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

    async def get_assigned_period(
        self,
        assignee_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[Task]:
        """Get all tasks assigned to a user for a specified period."""
        stmt = select(Task).where(
            and_(
                Task.assignee_id == assignee_id,
                func.date(Task.due_date) >= start_date,
                func.date(Task.due_date) <= end_date,
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_grades_assigned_period(
        self,
        assignee_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[tuple[str, int]]:
        """Get task titles and grades assigned to a user.

        For a specified period.
        """
        stmt = select(Task.title, Task.grade).where(
            and_(
                Task.assignee_id == assignee_id,
                func.date(Task.due_date) >= start_date,
                func.date(Task.due_date) <= end_date,
            )
        )
        result = await self._session.execute(stmt)
        return [(row.title, row.grade) for row in result]

    async def get_avg_grade_period(
        self,
        assignee_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal | None:
        """Get average grade of user tasks for a specified period."""
        # сопоставление для SQL CASE
        grade_mapping = {grade.name: grade.value for grade in TaskGrade}

        # SQL CASE выражение, чтобы преобразовать значения ENUM в числа
        int_grade_expression: ColumnElement[int | None] = case(
            grade_mapping,
            value=cast(Task.grade, String),  # ENUM в строку для сравнения CASE
            else_=None,  # если нет совпадения, будет NULL
        )

        stmt = select(
            func.round(func.avg(int_grade_expression), 4).label("avg_grade")
        ).where(
            and_(
                Task.assignee_id == assignee_id,
                func.date(Task.due_date) >= start_date,
                func.date(Task.due_date) <= end_date,
                Task.grade.is_not(None),  # отфильтровываем задачи без оценки
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_avg_grade_period_command(
        self,
        command_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal | None:
        """Get average grade of command for a specified period."""
        # выражение для преобразования TaskGrade ENUM в числовое значение
        grade_mapping = {grade.name: grade.value for grade in TaskGrade}
        int_grade_expression: ColumnElement[int | None] = case(
            grade_mapping,
            value=cast(Task.grade, String),
            else_=None,
        )

        # подзапрос: вычислить среднюю оценку каждого пользователя в команде
        user_avg_grade_subq = (
            select(func.avg(int_grade_expression).label("user_avg_grade"))
            .join(User, User.id == Task.assignee_id)
            .where(
                and_(
                    User.command_id == command_id,
                    func.date(Task.due_date) >= start_date,
                    func.date(Task.due_date) <= end_date,
                    Task.grade.is_not(None),
                )
            )
            .group_by(Task.assignee_id)
            .subquery("user_avg_grades_subq")
        )

        # основной запрос: вычисляем среднее от средних оценок пользователей
        stmt = select(
            func.round(
                func.avg(user_avg_grade_subq.c.user_avg_grade), 4
            ).label("command_avg_grade")
        )

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, task: Task) -> None:
        """Add a new Task object to session."""
        self._session.add(task)
        await self._session.flush([task])


class SATaskCommentRepo(AbsTaskCommentRepo):
    """Implementation of task comments repository using sqlalchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize a TaskComment Repository."""
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
            .options(selectinload(TaskComment.child_comments))  # type: ignore
            .where(TaskComment.id == taskcomment_id)
            .order_by(TaskComment.created_at)
        )
        return result.scalar_one_or_none()

    async def add(self, taskcomment: TaskComment) -> None:
        """Add a new TaskComment object to session."""
        self._session.add(taskcomment)
        await self._session.flush([taskcomment])


class SACalendarEventRepo(AbsCalendarEventRepo):
    """Implementation of calendar events repository using sqlalchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize a CalendarEvent Repository."""
        self._session = session

    async def get_by_id(self, c_event_id: uuid.UUID) -> CalendarEvent | None:
        """Get CalendarEvent by its ID."""
        result = await self._session.execute(
            select(CalendarEvent).where(CalendarEvent.id == c_event_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_detail(
        self,
        c_event_id: uuid.UUID,
    ) -> CalendarEvent | None:
        """Get CalendarEvent by its ID. Load all relationships."""
        result = await self._session.execute(
            select(CalendarEvent)
            .options(*load_all_relationships(CalendarEvent))
            .where(CalendarEvent.id == c_event_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_all_period(
        self,
        start_date: date,
        end_date: date,
    ) -> list[CalendarEvent]:
        """Get list of CalendarEvent objects for the specified period."""
        stmt = (
            select(CalendarEvent)
            .where(
                and_(
                    func.date(CalendarEvent.start_time) >= start_date,
                    func.date(CalendarEvent.end_time) <= end_date,
                )
            )
            .order_by(CalendarEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, c_event: CalendarEvent) -> None:
        """Add CalendarEvent object to session."""
        self._session.add(c_event)
        await self._session.flush([c_event])

    async def check_overlap_users(
        self,
        start_time: datetime,
        end_time: datetime,
        user_ids: set[uuid.UUID],
        event_id: uuid.UUID,
    ) -> uuid.UUID | None:
        """Check if existing user events overlap with the new event."""
        stmt = (
            select(CalendarEvent.id)
            .join(users_calendar_events_table)
            .where(
                and_(
                    users_calendar_events_table.c.user_id.in_(user_ids),
                    not_(CalendarEvent.id == event_id),
                    and_(
                        CalendarEvent.start_time < end_time,
                        CalendarEvent.end_time > start_time,
                    ),
                )
            )
        ).limit(1)

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class SAMeetingRepo(AbsMeetingRepo):
    """Implementation of meeting using sqlalchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize a Meeting Repository."""
        self._session = session

    async def get_by_id(self, meeting_id: uuid.UUID) -> Meeting | None:
        """Get Meeting by its ID."""
        result = await self._session.execute(
            select(Meeting).where(Meeting.id == meeting_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_detail(self, meeting_id: uuid.UUID) -> Meeting | None:
        """Get Meeting by its ID. Load all relationships."""
        result = await self._session.execute(
            select(Meeting)
            .options(
                selectinload(Meeting.members),
                selectinload(Meeting.creator),
                selectinload(Meeting.command),
                joinedload(Meeting.calendar_event).selectinload(
                    CalendarEvent.users
                ),
            )
            .where(Meeting.id == meeting_id)
        )
        return result.unique().scalar_one_or_none()

    async def add(self, meeting: Meeting) -> None:
        """Add Meeting object to session."""
        self._session.add(meeting)
        await self._session.flush()
