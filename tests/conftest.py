"""Pytest configuration settings."""

import asyncio
from typing import Any, AsyncGenerator

import pytest
from faker import Faker
from httpx import ASGITransport, AsyncClient, Response
from pytest import FixtureRequest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from project.app_admin.create_master import create_master
from project.app_auth.application.schemas import UserCreate
from project.app_auth.domain.models import Profile, User  # noqa
from project.app_org.domain.models import (  # noqa
    Command,
    Department,
    News,
    Role,
)
from project.config import settings
from project.core.db.base import Base
from project.core.log_config import get_logger
from project.main import app
from tests.helpers import get_auth_token
from tests.setup_teardown_db import (
    setup_db_before_tests,
    teardown_db_after_tests,
)

logger = get_logger(__name__)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Integrate anyio into pytest."""
    return "asyncio"


@pytest.fixture(scope="session")
async def db_engine(
    request: FixtureRequest,
    _session_event_loop: asyncio.AbstractEventLoop,
) -> AsyncEngine:
    """Create the test DB engine for the test session.

    Handle teardown using 'addfinalizer'.

    Args:
        request (FixtureRequest): Pytest fixture request object;
            used to register a finalizer ('addfinalizer').
        _session_event_loop (asyncio.AbstractEventLoop): Asyncio session event
            loop (provided by pytest-asyncio) is required to correctly run the
            async finalizer via `run_until_complete` at the end of the session.

    Returns:
        AsyncEngine: SQLAlchemy async engine connected to the test database.
    """
    test_engine: AsyncEngine | None = None
    loop = _session_event_loop

    try:
        await setup_db_before_tests()
        test_engine = create_async_engine(url=settings.DB.url_async)
        logger.info("Test engine created successfully.")

        async def async_finalizer() -> None:
            """Final teardown to realize resources."""
            logger.info("Running final database teardown (finalizer)")
            await teardown_db_after_tests()
            logger.info("Final database teardown completed (finalizer)")

        def sync_finalizer_wrapper() -> None:
            """Sync wrapper to use async_finalizer into the event loop."""
            logger.info("Running 'sync_finalizer_wrapper'")
            try:
                loop.run_until_complete(async_finalizer())
                # можно и так, если нужно вызвать только одну корутину:
                # loop.run_until_complete(teardown_db_after_tests())
                logger.info("'sync_finalizer_wrapper' finished successfully.")
            except Exception:  # noqa
                logger.exception("Exception during finalizer execution")

        request.addfinalizer(sync_finalizer_wrapper)

        return test_engine

    except Exception as e:  # noqa
        logger.exception("Critical error during db_engine setup")
        if test_engine:
            try:
                await test_engine.dispose()
            except Exception as dispose_err:  # noqa
                logger.error(
                    "Error disposing engine after setup failure: '%s'",
                    dispose_err,
                )

        logger.warning("Attempting cleanup after failed setup")
        try:
            await teardown_db_after_tests()
        except Exception as cleanup_e:  # noqa
            logger.error(
                "Error during cleanup after failed setup: %s", cleanup_e
            )
        pytest.fail(f"Failed to configure test environment: {e}")
        raise  # исходная ошибка настройки, чтобы тесты не запустились


@pytest.fixture(scope="function")
async def truncate_tables(
    db_engine: AsyncEngine,
) -> AsyncGenerator[None, None]:
    """Clear all tables managed by 'Base.metadata' before each test.

    Relies on transaction rollback in db_session for primary isolation.
    This provides an extra layer of safety.

    Args:
        db_engine (AsyncEngine): Configured async test engine.

    Yields:
        Iterator[AsyncGenerator[None, None]]: Transfer control to the test.
    """
    logger.info("Start clearing tables (TRUNCATE) before test")
    table_names: list[str] = list(Base.metadata.tables.keys())

    if not table_names:
        logger.warning("No tables found in 'Base.metadata' to truncate.")
        yield  # просто выполняем тест, если таблиц нет
        return  # чтобы управление не вернулось снова сюда после теста

    quoted_table_names = [f'"{name}"' for name in table_names]
    truncate_sql = text(
        f"TRUNCATE TABLE {', '.join(quoted_table_names)} "
        "RESTART IDENTITY CASCADE;"
        # CASCADE для рекурсивного удаления связанных внешних ключей
    )
    logger.info("Truncating tables: %s", ", ".join(table_names))
    try:
        # begin() для автоматического commit/rollback транзакции очистки
        async with db_engine.begin() as conn:
            logger.info("Run TRUNCATE on engine '%s'", db_engine)
            await conn.execute(truncate_sql)
        logger.info("Tables truncated successfully.")

        yield  # выполнение теста

    except Exception as e:  # noqa
        logger.exception("Error during table truncation: %s", e)
        pytest.fail(f"Failed to truncate tables: {e}")


@pytest.fixture(scope="function")
async def db_session(
    db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Async session without transaction management.

    Use this inside the UoW that controls transactions.

    Args:
        db_engine (AsyncEngine): Configured async test engine.

    Yields:
        Iterator[AsyncGenerator[AsyncSession, None]]: Opened async session.
    """
    async_session_maker = async_sessionmaker(
        bind=db_engine,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        session_id = id(session)
        logger.debug("Async test session '%s' created", session_id)
        try:
            yield session
        finally:
            logger.debug("Async test session '%s' closed", session_id)


@pytest.fixture(scope="function")
async def httpx_test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create HTTPX client for testing the FastAPI application.

    Yields:
        Iterator[AsyncGenerator[AsyncClient, None]]: Configured HTTPX client.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture(scope="function")
async def get_master_token(
    httpx_test_client: AsyncClient,
) -> str:
    """Create master user and return master auth token."""
    await create_master()
    response = await httpx_test_client.post(
        url=f"{settings.AUTH.PREFIX_AUTH}/login/",
        data={
            "username": settings.MASTER_EMAIL,
            "password": settings.MASTER_PASSWORD,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def fake_instance() -> Faker:
    """Get Faker instance."""
    return Faker()


@pytest.fixture(scope="function")
def fake_user_schema(fake_instance: Faker) -> UserCreate:
    """Define the fake user for tests."""
    return UserCreate(
        email=fake_instance.email(),
        password=fake_instance.password(),
    )


@pytest.fixture(scope="function")
async def authenticated_user(
    httpx_test_client: AsyncClient,
    fake_user_schema: UserCreate,
) -> dict[str, Any]:
    """Create new user and return this user data."""
    response: Response = await httpx_test_client.post(
        url=f"{settings.AUTH.PREFIX_AUTH}/register/",
        json=fake_user_schema.model_dump(),
    )
    assert response.status_code == 201

    new_user_data: dict = response.json()
    token = await get_auth_token(
        httpx_client=httpx_test_client,
        email=fake_user_schema.email,
        password=fake_user_schema.password,
    )

    return {"user": new_user_data, "token": token}
