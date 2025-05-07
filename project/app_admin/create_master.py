"""Create master user."""

import asyncio
from typing import Any, Literal

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from project.app_auth.domain.models import User
from project.app_auth.infrastructure.security import get_password_hasher
from project.app_org.domain.models import Command
from project.config import settings
from project.core.db.setup import AsyncSessionFactory
from project.core.log_config import get_logger

logger = get_logger(__name__)


def check_table(sync_session: Any) -> bool:
    """Check if table exists. Synchronous helper."""
    bind = sync_session.get_bind()
    inspector = inspect(bind)
    return inspector.has_table(User.__tablename__)


async def create_master_command(
    session: AsyncSession,
) -> Command | Literal[False]:
    """Create a master command if not exists.."""
    if not await session.run_sync(check_table):
        logger.error("Table '%s' doesn't exist", User.__tablename__)
        return False

    master_command_name = settings.MASTER_COMMAND_NAME
    if not master_command_name:
        logger.error("Master command name is empty!")
        return False

    result = await session.execute(
        select(Command).where(Command.name == master_command_name)
    )
    command: Command | None = result.scalar_one_or_none()
    if command:
        logger.info("Command '%s' already exists", master_command_name)
        return command

    command = Command(
        name=master_command_name,
        description="Master command",
    )

    session.add(command)
    await session.flush()
    return command


async def create_master() -> bool:
    """Create a master user if not exists.."""
    async with AsyncSessionFactory() as session:
        master_command: Command | Literal[False] = await create_master_command(
            session
        )
        if not master_command:
            logger.error("Master command doesn't exist!")
            return False

        master_email: str = settings.MASTER_EMAIL
        master_password: str = settings.MASTER_PASSWORD

        if not master_email or not master_password:
            logger.error("Master email or master password is empty!")
            return False

        result = await session.execute(
            select(User).where(User.email == master_email)
        )
        master: User | None = result.scalar_one_or_none()
        if master:
            logger.info("Master '%s' already exists", master_email)
            return True

        session.add(
            User(
                email=master_email,
                plain_password=master_password,
                command_id=master_command.id,
                hasher=get_password_hasher(),
            )
        )
        await session.commit()
        logger.info("Master '%s' created", master_email)
        return True


if __name__ == "__main__":
    asyncio.run(create_master())
