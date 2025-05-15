"""Project tasks to run in background."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, delete
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from project.app_auth.domain.models import User
from project.background.celery_app import celery_app
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)


@celery_app.W
async def clear_old_deactivated() -> None:
    """Drop from DB users that deactivated more than 30 days."""
    logger.info("Start clear_old_deactivated task.")

    engine = create_async_engine(url=settings.DB.url_async)
    LocalAsyncSessFact = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    try:
        async with LocalAsyncSessFact() as session:
            async with session.begin():
                now_utc = datetime.now(timezone.utc)
                thirty_days_ago = now_utc - timedelta(days=30)
                stmt = delete(User).where(
                    and_(
                        User.updated_at < thirty_days_ago,
                        User.is_active.is_(False),
                    )
                )

                result = await session.execute(stmt)
                deleted_count = result.rowcount
                logger.info("Dropped %d inactive users.", deleted_count)

        logger.info("Task clear_old_deactivated completed.")

    except Exception:
        logger.exception("Error in clear_old_deactivated task")
        raise
    finally:
        await engine.dispose()
