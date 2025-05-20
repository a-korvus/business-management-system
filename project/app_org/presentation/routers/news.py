"""News router in the 'app_org'."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from project.app_auth.domain.models import User
from project.app_auth.presentation.dependencies import get_admin
from project.app_org.application.schemas import (
    NewsCreate,
    NewsRead,
    NewsUpdate,
)
from project.app_org.application.services.news import NewsService
from project.app_org.domain.exceptions import NewsNotFound
from project.app_org.domain.models import News
from project.app_org.presentation.dependencies import get_news_service
from project.config import settings
from project.core.log_config import get_logger
from project.core.schemas import Pagination

logger = get_logger(__name__)

router = APIRouter(
    prefix=f"{settings.PREFIX_ORG}/news",
    tags=["org", "news"],
)


@router.post(
    path="/",
    response_model=NewsRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new post.",
    description="Create a new information post in the organization.",
)
async def new_post(
    data: NewsCreate,
    news_service: Annotated[NewsService, Depends(get_news_service)],
    admin: Annotated[User, Depends(get_admin)],
) -> News:
    """Create a new information post."""
    try:
        return await news_service.create(data)
    except ValueError as e:  # ошибки валидации из домена
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:  # любые непредвиденные ошибки # noqa
        logger.exception("Unexpected error while creating new post.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while creating new post.",
        )


@router.get(
    path="/",
    response_model=list[NewsRead],
    status_code=status.HTTP_200_OK,
    summary="Get news.",
    description="Get all information posts in the organization.",
)
async def get_news(
    pagination: Annotated[Pagination, Query()],
    news_service: Annotated[NewsService, Depends(get_news_service)],
) -> list[News]:
    """Get all posts."""
    try:
        return await news_service.get_all(pagination.offset, pagination.limit)
    except Exception:  # noqa
        logger.exception("Unexpected error while retrieving all messages.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while retrieving all messages.",
        )


@router.get(
    path="/{post_id}/",
    response_model=NewsRead,
    status_code=status.HTTP_200_OK,
    summary="Get post.",
    description="Get the information post by its ID.",
)
async def get_news_post(
    post_id: uuid.UUID,
    news_service: Annotated[NewsService, Depends(get_news_service)],
) -> News | None:
    """Get the post by ID."""
    try:
        return await news_service.get_by_id(post_id)
    except Exception:  # noqa
        logger.exception("Unexpected error while retrieving the post.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while retrieving the post.",
        )


@router.put(
    path="/{post_id}/",
    response_model=NewsRead,
    status_code=status.HTTP_200_OK,
    summary="Update post.",
    description="Update the information post data by its ID.",
)
async def update_post(
    post_id: uuid.UUID,
    updating_data: NewsUpdate,
    news_service: Annotated[NewsService, Depends(get_news_service)],
    admin: Annotated[User, Depends(get_admin)],
) -> News:
    """Update the post by ID."""
    try:
        return await news_service.update(news_id=post_id, data=updating_data)
    except NewsNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:  # ошибки валидации
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:  # noqa
        logger.exception("Unexpected error while updating the post.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while updating the post.",
        )
