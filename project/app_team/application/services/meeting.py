"""Meeting-related service in 'app_team'."""

import uuid

from project.app_auth.domain.exceptions import UserNotFound
from project.app_org.domain.exceptions import CommandNotFound
from project.app_team.application.schemas import MeetingCreate, MeetingUpdate
from project.app_team.domain.exceptions import MeetingNotFound, OverlapError
from project.app_team.domain.models import Meeting
from project.app_team.infrastructure.unit_of_work import SATeamUnitOfWork
from project.core.log_config import get_logger

logger = get_logger(__name__)


class MeetingService:
    """Application service for managing meetings."""

    def __init__(self, uow: SATeamUnitOfWork) -> None:
        """Initialize the service object. Set UoW."""
        self.uow = uow
        logger.debug("'%s' initialized", self.__class__.__name__)

    async def get_by_id(self, meeting_id: uuid.UUID) -> Meeting | None:
        """Get Meeting by its ID."""
        async with self.uow as uow:
            return await uow.meetings.get_by_id(meeting_id)

    async def get_by_id_detail(self, meeting_id: uuid.UUID) -> Meeting | None:
        """Get Meeting by its ID. Load all relationships."""
        async with self.uow as uow:
            return await uow.meetings.get_by_id_detail(meeting_id)

    async def create(self, data: MeetingCreate) -> Meeting:
        """Create a new meeting.

        Related calendar event is also created here.
        """
        async with self.uow as uow:
            if not await uow.partners.get_by_id(data.creator_id):
                raise UserNotFound(user_id=data.creator_id)

            if not await uow.partners.get_command_by_id(data.command_id):
                raise CommandNotFound(command_id=data.command_id)

            if not await uow.partners.user_share_command_id(
                user_ids=data.members_ids,
                target_command_id=data.command_id,
            ):
                raise ValueError("Members don't belong to the same command.")

            members = await uow.partners.users_in_seq(data.members_ids)
            members_ids = [user.id for user in members]

            meeting_data = data.model_dump(exclude={"members_ids"})
            meeting_data["meet_members"] = members
            meeting = Meeting(**meeting_data)
            await uow.meetings.add(meeting)

            overlap = await uow.events.check_overlap_users(
                start_time=data.start_time,
                end_time=data.end_time,
                user_ids=set(members_ids),
                event_id=meeting.calendar_event.id,
            )
            if overlap:
                raise OverlapError(meeting.calendar_event.id)

            await uow.commit()
            return meeting

    async def update(
        self,
        meeting_id: uuid.UUID,
        data: MeetingUpdate,
    ) -> Meeting:
        """Update the meeting."""
        async with self.uow as uow:
            meeting: Meeting | None = await uow.meetings.get_by_id(meeting_id)
            if not meeting:
                logger.warning("Meeting with id '%s' not found", meeting_id)
                raise MeetingNotFound(meeting_id)

            upd_data: dict = data.model_dump(exclude_unset=True)

            for field_name, field_value in upd_data.items():
                setattr(meeting, field_name, field_value)

            if upd_data:
                await uow.commit()
                await uow.refresh(meeting)

            return meeting

    async def deactivate(self, meeting_id: uuid.UUID) -> bool:
        """Deactivate the meeting."""
        async with self.uow as uow:
            meeting: Meeting | None = await uow.meetings.get_by_id(meeting_id)
            if not meeting:
                raise MeetingNotFound(meeting_id)

            if meeting.is_active:
                meeting.is_active = False
                await uow.commit()

            return True

    async def include_users(
        self,
        meeting_id: uuid.UUID,
        user_ids: list[uuid.UUID],
    ) -> Meeting:
        """Add users to the meeting."""
        async with self.uow as uow:
            meeting: Meeting | None = await uow.meetings.get_by_id_detail(
                meeting_id=meeting_id,
            )
            if not meeting:
                raise MeetingNotFound(meeting_id)

            existing_ids = [user.id for user in meeting.members]
            uq_new_ids = set(user_ids) - set(existing_ids)

            if not uq_new_ids:
                return meeting

            overlap = await uow.events.check_overlap_users(
                start_time=meeting.start_time,
                end_time=meeting.end_time,
                user_ids=uq_new_ids,
                event_id=meeting.calendar_event.id,
            )
            if overlap:
                raise OverlapError(meeting.calendar_event.id)

            if not await uow.partners.user_share_command_id(
                user_ids=uq_new_ids,
                target_command_id=meeting.command_id,
            ):
                raise ValueError("Members don't belong to the same command.")

            new_members = await uow.partners.users_in_seq(uq_new_ids)
            meeting.add_members(new_members)
            await uow.commit()

            return meeting
