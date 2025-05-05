"""Test API routs for 'news' router."""

import random

import pytest
from httpx import AsyncClient, Response

from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("truncate_tables")]

ORG_PREFIX = settings.PREFIX_ORG


async def test_new_post(
    httpx_test_client: AsyncClient,
    fake_news_data: dict,
) -> None:
    """Test creating a new post."""
    response: Response = await httpx_test_client.post(
        url=f"{ORG_PREFIX}/news/",
        json=fake_news_data,
    )

    assert response.status_code == 201

    response_data = response.json()

    assert isinstance(response_data, dict)
    assert response_data.get("id") is not None
    assert response_data.get("text") == fake_news_data["text"]


async def test_get_news(
    httpx_test_client: AsyncClient,
    fake_news_data: dict,
) -> None:
    """Test retrieving all news."""
    news_count = 0
    for _ in range(random.randint(10, 20)):
        response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/news/",
            json=fake_news_data,
        )

        assert response_create.status_code == 201

        news_count += 1

    response_get: Response = await httpx_test_client.get(f"{ORG_PREFIX}/news/")
    response_data = response_get.json()

    assert isinstance(response_data, list)
    assert news_count == len(response_data)
    for post in response_data:
        assert isinstance(post, dict)
        assert post.get("id") is not None


async def test_get_news_post(
    httpx_test_client: AsyncClient,
    fake_news_data: dict,
) -> None:
    """Test retrieving the post."""
    news = list()
    for _ in range(random.randint(10, 20)):
        response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/news/",
            json=fake_news_data,
        )

        assert response_create.status_code == 201

        response_create_data = response_create.json()

        assert isinstance(response_create_data, dict)

        news.append(response_create_data)

    for post in news:
        post_id = post.get("id")

        assert post_id is not None

        response_get = await httpx_test_client.get(
            url=f"{ORG_PREFIX}/news/{post_id}/",
        )

        assert response_get.status_code == 200

        response_get_data = response_get.json()

        assert isinstance(response_get_data, dict)
        assert response_get_data.get("id") == post_id
        assert response_get_data.get("created_at") is not None
        assert response_get_data.get("updated_at") is not None


async def test_update_post(
    httpx_test_client: AsyncClient,
    fake_news_data: dict,
) -> None:
    """Test updating the post."""
    news = list()
    for _ in range(random.randint(10, 20)):
        response_create: Response = await httpx_test_client.post(
            url=f"{ORG_PREFIX}/news/",
            json=fake_news_data,
        )

        assert response_create.status_code == 201

        response_create_data = response_create.json()

        assert isinstance(response_create_data, dict)

        news.append(response_create_data)

    updating_data = {
        "text": fake_news_data["text"][:-100],
    }
    some_existing_post: dict = random.choice(news)
    some_post_id = some_existing_post.get("id")

    assert some_post_id is not None

    response_update = await httpx_test_client.put(
        url=f"{ORG_PREFIX}/news/{some_post_id}/",
        json=updating_data,
    )

    assert response_update.status_code == 200

    response_update_data = response_update.json()

    assert isinstance(response_update_data, dict)
    assert some_post_id == response_update_data.get("id")
    assert some_existing_post["text"] != response_update_data["text"]
    assert updating_data["text"] == response_update_data["text"]
