"""Task-related service in 'app_team'."""

import uuid
from decimal import Decimal
from typing import Literal

from project.app_auth.domain.exceptions import UserNotFound
from project.app_team.application.schemas import (
    Period,
    TaskCreate,
    TaskUpdate,
)
from project.app_team.domain.exceptions import (
    CalendarEventNotFound,
    TaskNotFound,
)
from project.app_team.domain.models import Task
from project.app_team.infrastructure.unit_of_work import SATeamUnitOfWork
from project.core.log_config import get_logger

logger = get_logger(__name__)


class TaskService:
    """Application service for managing tasks."""

    def __init__(self, uow: SATeamUnitOfWork) -> None:
        """Initialize the service object. Set UoW."""
        self.uow = uow
        logger.debug("'%s' initialized", self.__class__.__name__)

    async def get_task_comments(self, task_id: uuid.UUID) -> Task:
        """Get a task with comments."""
        async with self.uow as uow:
            task = await uow.tasks.get_by_id_comments(task_id)
            if not task or not task.is_active:
                raise TaskNotFound(task_id)

            return task

    async def get_assigned_tasks(
        self,
        assignee_id: uuid.UUID,
        period: Period,
    ) -> list[Task]:
        """Get tasks assigned to a user for a period."""
        async with self.uow as uow:
            assignee = await uow.partners.get_by_id(assignee_id)
            if not assignee:
                raise UserNotFound(user_id=assignee_id)

            return await uow.tasks.get_assigned_period(
                assignee_id=assignee_id,
                start_date=period.start,
                end_date=period.end,
            )

    async def get_grades_assigned_tasks(
        self,
        assignee_id: uuid.UUID,
        period: Period,
    ) -> list[tuple[str, int]]:
        """Get task titles assigned to a user for a period and its grades.

        Tasks without a grade will not be selected.
        """
        async with self.uow as uow:
            assignee = await uow.partners.get_by_id(assignee_id)
            if not assignee:
                raise UserNotFound(user_id=assignee_id)

            return await uow.tasks.get_grades_assigned_period(
                assignee_id=assignee_id,
                start_date=period.start,
                end_date=period.end,
            )

    async def get_avg_grade_period(
        self,
        assignee_id: uuid.UUID,
        period: Period,
    ) -> Decimal | None:
        """Get average grade of user tasks for a specified period."""
        async with self.uow as uow:
            assignee = await uow.partners.get_by_id(assignee_id)
            if not assignee:
                raise UserNotFound(user_id=assignee_id)

            return await uow.tasks.get_avg_grade_period(
                assignee_id=assignee_id,
                start_date=period.start,
                end_date=period.end,
            )

    async def get_avg_grade_period_command(
        self,
        assignee_id: uuid.UUID,
        period: Period,
    ) -> Decimal | None:
        """Get average grade of user command for a specified period."""
        async with self.uow as uow:
            assignee = await uow.partners.get_by_id(assignee_id)
            if not assignee:
                raise UserNotFound(user_id=assignee_id)

            command_id = await uow.partners.get_command_by_user_id(assignee_id)
            if not command_id:
                return None

            return await uow.tasks.get_avg_grade_period_command(
                command_id=command_id,
                start_date=period.start,
                end_date=period.end,
            )

    async def create_assignment(self, data: TaskCreate) -> Task:
        """Create a task. Assing to user."""
        async with self.uow as uow:
            creator = await uow.partners.get_by_id(data.creator_id)
            if not creator:
                raise UserNotFound(user_id=data.creator_id)
            assignee = await uow.partners.get_by_id(data.assignee_id)
            if not assignee:
                raise UserNotFound(user_id=data.assignee_id)

            if data.calendar_event_id and not await uow.events.get_by_id(
                data.calendar_event_id
            ):
                raise CalendarEventNotFound(data.calendar_event_id)

            new_task = Task(**data.model_dump())
            await uow.tasks.add(new_task)
            await uow.commit()

            return new_task

    async def update_task(self, task_id: uuid.UUID, data: TaskUpdate) -> Task:
        """Update existing task."""
        async with self.uow as uow:
            task = await uow.tasks.get_by_id(task_id)
            if not task or not task.is_active:
                raise TaskNotFound(task_id)
            if data.assignee_id and not await uow.partners.get_by_id(
                data.assignee_id
            ):
                raise UserNotFound(user_id=data.assignee_id)
            if data.calendar_event_id and not await uow.events.get_by_id(
                data.calendar_event_id
            ):
                raise CalendarEventNotFound(data.calendar_event_id)

            update_data: dict = data.model_dump(exclude_unset=True)
            needs_update = False

            for field_name, field_value in update_data.items():
                if getattr(task, field_name) != field_value:
                    setattr(task, field_name, field_value)
                    needs_update = True

            if needs_update:
                await self.uow.commit()
                await self.uow.refresh(task)

            return task

    async def deactivate_task(self, task_id: uuid.UUID) -> Literal[True]:
        """Deactivate task."""
        async with self.uow as uow:
            task = await uow.tasks.get_by_id(task_id)
            if not task or not task.is_active:
                raise TaskNotFound(task_id)

            task.is_active = False
            await uow.commit()

            return True
