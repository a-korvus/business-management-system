"""News-related service in 'app_org'."""

import uuid

from project.app_org.application.schemas import NewsCreate, NewsUpdate
from project.app_org.domain.exceptions import NewsNotFound
from project.app_org.domain.models import News
from project.app_org.infrastructure.unit_of_work import SAOrgUnitOfWork
from project.core.log_config import get_logger

logger = get_logger(__name__)


class NewsService:
    """Application service for managing news."""

    def __init__(self, uow: SAOrgUnitOfWork) -> None:
        """Initialize the service object. Set UoW."""
        self.uow = uow
        logger.debug("'%s' initialized", self.__class__.__name__)

    async def get_by_id(self, news_id: uuid.UUID) -> News | None:
        """Get news by ID."""
        async with self.uow as uow:
            return await uow.news.get_by_id(news_id)

    async def get_all(self, offset: int, limit: int) -> list[News]:
        """Get all news from DB."""
        async with self.uow as uow:
            return await uow.news.list_all(offset, limit)

    async def create(self, data: NewsCreate) -> News:
        """Create a new News instance."""
        async with self.uow as uow:
            new_news = News(**data.model_dump())
            await uow.news.add(new_news)
            await uow.commit()

            return new_news

    async def update(
        self,
        news_id: uuid.UUID,
        data: NewsUpdate,
    ) -> News:
        """Update the News info."""
        async with self.uow as uow:
            upd_news = await uow.news.get_by_id(news_id)
            if not upd_news:
                logger.warning("Post with id '%s' not found", news_id)
                raise NewsNotFound(news_id=news_id)

            update_data: dict = data.model_dump(exclude_unset=True)
            for field_name, field_value in update_data.items():
                setattr(upd_news, field_name, field_value)

            if update_data:
                await uow.commit()
                await uow.refresh(upd_news)
                logger.debug(
                    "News instance '%s' refreshed after update.", news_id
                )

            return upd_news
