"""Test NewsService from 'app_org' app."""

import random
from typing import Callable

import pytest
from faker import Faker

from project.app_org.application.interfaces import AbsUnitOfWork
from project.app_org.application.schemas import NewsCreate, NewsUpdate
from project.app_org.application.services.news import NewsService
from project.app_org.domain.models import News
from project.core.log_config import get_logger

logger = get_logger(__name__)

pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]


async def test_create(
    verify_news_service: NewsService,
    fake_news_schema: NewsCreate,
) -> None:
    """Test creating a new post instance."""
    new_post = await verify_news_service.create(data=fake_news_schema)

    assert isinstance(new_post, News)
    assert new_post.id is not None


async def test_get_by_id(
    verify_news_service: NewsService,
    fake_news_schema: NewsCreate,
    uow_sess_factory: Callable[[], AbsUnitOfWork],
) -> None:
    """Test retrieving the existing post instance."""
    alter_news_service = NewsService(uow=uow_sess_factory())
    new_post = await alter_news_service.create(data=fake_news_schema)

    assert isinstance(new_post, News)

    existing_post = await verify_news_service.get_by_id(news_id=new_post.id)

    assert isinstance(existing_post, News)
    assert new_post.id == existing_post.id
    assert new_post.text == existing_post.text


async def test_get_all(
    verify_news_service: NewsService,
    fake_news_schema: NewsCreate,
    uow_sess_factory: Callable[[], AbsUnitOfWork],
) -> None:
    """Test retrieving all existing post instance."""
    post_count = 0
    for _ in range(random.randint(10, 30)):
        alter_news_service = NewsService(uow=uow_sess_factory())
        await alter_news_service.create(data=fake_news_schema)
        post_count += 1

    posts = await verify_news_service.get_all()

    assert isinstance(posts, list)
    assert post_count == len(posts)


async def test_update(
    verify_news_service: NewsService,
    fake_news_schema: NewsCreate,
    uow_sess_factory: Callable[[], AbsUnitOfWork],
    fake_instance: Faker,
) -> None:
    """Test updating the existing post."""
    alter_news_service = NewsService(uow=uow_sess_factory())
    new_post = await alter_news_service.create(data=fake_news_schema)

    assert isinstance(new_post, News)

    updating_data = NewsUpdate(
        text=fake_instance.text(max_nb_chars=5000),
    )
    updated_post = await verify_news_service.update(
        news_id=new_post.id,
        data=updating_data,
    )

    assert isinstance(updated_post, News)
    assert new_post.id == updated_post.id
    assert new_post.text != updated_post.text
    assert updating_data.text == updated_post.text
