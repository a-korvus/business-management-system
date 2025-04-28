"""Create master user."""

import asyncio
from typing import Any

from sqlalchemy import inspect, select

from project.app_auth.domain.models import User
from project.app_auth.presentation.dependencies import get_password_hasher
from project.config import settings
from project.core.db.setup import AsyncSessionFactory
from project.core.log_config import get_logger

logger = get_logger(__name__)


def check_table(sync_session: Any) -> bool:
    """Check if table exists. Synchronous helper."""
    bind = sync_session.get_bind()
    inspector = inspect(bind)
    return inspector.has_table(User.__tablename__)


async def create_master() -> bool:
    """Create a master user if not exists.."""
    async with AsyncSessionFactory() as session:
        if not await session.run_sync(check_table):
            logger.error("Table '%s' doesn't exist", User.__tablename__)
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
                hasher=get_password_hasher(),
            )
        )
        await session.commit()
        logger.info("Master '%s' created", master_email)
        return True


if __name__ == "__main__":
    asyncio.run(create_master())
