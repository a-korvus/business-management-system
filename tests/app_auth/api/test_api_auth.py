"""Test API routs for 'auth' router."""

import uuid
from typing import Callable

import pytest
from httpx import AsyncClient, Response

from project.app_auth.application.schemas import UserCreate
from project.app_auth.domain.models import User
from project.app_auth.infrastructure.unit_of_work import SAAuthUnitOfWork
from project.config import settings
from project.core.log_config import get_logger

logger = get_logger(__name__)

AUTH_PREFIX = settings.AUTH.PREFIX_AUTH

pytestmark = pytest.mark.anyio


@pytest.mark.usefixtures("truncate_tables")
async def test_register(
    httpx_test_client: AsyncClient,
    uow_factory: Callable[[], SAAuthUnitOfWork],
    fake_user_schema: UserCreate,
) -> None:
    """Test register new user route."""
    # отправляем на ручку данные для регистрации нового пользователя
    response: Response = await httpx_test_client.post(
        url=f"{AUTH_PREFIX}/register/",
        json=fake_user_schema.model_dump(),
    )

    assert response.status_code == 201

    response_data = response.json()

    # проверяем, что пришло в ответе
    assert response_data["email"] == fake_user_schema.email
    assert "id" in response_data
    assert response_data["is_active"] is True

    async with uow_factory() as uow:
        registered_user = await uow.users.get_by_email(
            email=fake_user_schema.email,
        )
        assert isinstance(registered_user, User)
        assert str(registered_user.id) == response_data["id"]
        assert registered_user.hashed_password is not None
        assert registered_user.hashed_password != fake_user_schema.password


@pytest.mark.usefixtures("truncate_tables")
async def test_register_duplicate_email(
    httpx_test_client: AsyncClient,
    fake_user_schema: UserCreate,
) -> None:
    """Test registration with existing email."""
    user_data = fake_user_schema.model_dump()
    url = f"{AUTH_PREFIX}/register/"

    response: Response = await httpx_test_client.post(url, json=user_data)
    assert response.status_code == 201

    duplicate_response: Response = await httpx_test_client.post(
        url=url,
        json=user_data,
    )

    assert duplicate_response.status_code == 400
    assert "already registered" in duplicate_response.json()["detail"]


@pytest.mark.usefixtures("truncate_tables")
async def test_login(
    httpx_test_client: AsyncClient,
    fake_user_schema: UserCreate,
) -> None:
    """Test login successful."""
    reg_url = f"{AUTH_PREFIX}/register/"
    reg_response: Response = await httpx_test_client.post(
        url=reg_url,
        json=fake_user_schema.model_dump(),
    )

    assert reg_response.status_code == 201

    login_url = f"{AUTH_PREFIX}/login/"
    login_form_data = {
        "username": fake_user_schema.email,
        "password": fake_user_schema.password,
    }
    login_response: Response = await httpx_test_client.post(
        url=login_url,
        data=login_form_data,
    )

    assert login_response.status_code == 200

    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.usefixtures("truncate_tables")
async def test_login_wrong_password(
    httpx_test_client: AsyncClient,
    fake_user_schema: UserCreate,
) -> None:
    """Test login with wrong password."""
    reg_url = f"{AUTH_PREFIX}/register/"
    reg_response: Response = await httpx_test_client.post(
        url=reg_url,
        json=fake_user_schema.model_dump(),
    )

    assert reg_response.status_code == 201

    login_url = f"{AUTH_PREFIX}/login/"
    login_form_data = {
        "username": fake_user_schema.email,
        "password": str(uuid.uuid4()),  # wrong password here
    }
    login_response: Response = await httpx_test_client.post(
        url=login_url,
        data=login_form_data,
    )

    assert login_response.status_code == 401
    assert "WWW-Authenticate" in login_response.headers


@pytest.mark.usefixtures("truncate_tables")
async def test_login_user_not_found(
    httpx_test_client: AsyncClient,
    fake_user_schema: UserCreate,
) -> None:
    """Test login as non-existent user."""
    login_url = f"{AUTH_PREFIX}/login/"
    login_form_data = {
        "username": fake_user_schema.email,
        "password": str(uuid.uuid4()),  # wrong password here
    }
    login_response: Response = await httpx_test_client.post(
        url=login_url,
        data=login_form_data,
    )

    assert login_response.status_code == 401
