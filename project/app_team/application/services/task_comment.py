"""Task comments-related service in 'app_team'."""

import uuid

from project.app_auth.domain.exceptions import UserNotFound
from project.app_team.application.schemas import (
    TaskCommentCreate,
    TaskCommentUpdate,
)
from project.app_team.domain.exceptions import (
    TaskCommentNotFound,
    TaskNotFound,
)
from project.app_team.domain.models import TaskComment
from project.app_team.infrastructure.unit_of_work import SATeamUnitOfWork
from project.core.log_config import get_logger

logger = get_logger(__name__)


class TaskCommentService:
    """Application service for managing task comments."""

    def __init__(self, uow: SATeamUnitOfWork) -> None:
        """Initialize the service object. Set UoW."""
        self.uow = uow
        logger.debug("'%s' initialized", self.__class__.__name__)

    async def create_comment(self, data: TaskCommentCreate) -> TaskComment:
        """Create a new comment."""
        async with self.uow as uow:
            task = await uow.tasks.get_by_id(data.task_id)
            if not task or not task.is_active:
                raise TaskNotFound(data.task_id)

            user = await uow.partners.get_by_id(data.commentator_id)
            if not user or not user.is_active:
                raise UserNotFound(user_id=data.commentator_id)

            if (
                data.parent_comment_id
                and not await uow.tasks_comments.get_by_id(
                    data.parent_comment_id
                )
            ):
                raise TaskCommentNotFound(data.parent_comment_id)

            comment = TaskComment(**data.model_dump())
            await uow.tasks_comments.add(comment)
            await uow.commit()

            return comment

    async def update_comment(
        self,
        comment_id: uuid.UUID,
        data: TaskCommentUpdate,
    ) -> TaskComment:
        """Update a comment."""
        async with self.uow as uow:
            comment = await uow.tasks_comments.get_by_id(comment_id)
            if not comment:
                logger.warning("Comment with id '%s' not found", comment_id)
                raise TaskCommentNotFound(comment_id)

            update_data: dict = data.model_dump(exclude_unset=True)

            for field_name, field_value in update_data.items():
                setattr(comment, field_name, field_value)

            if update_data:
                await self.uow.commit()
                await self.uow.refresh(comment)

            return comment
