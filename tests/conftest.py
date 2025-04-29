"""Pytest configuration settings."""

from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from project.app_auth.domain.models import Profile, User  # noqa
from project.app_org.domain.models import (  # noqa
    Command,
    Department,
    News,
    Role,
)
from project.core.db.base import Base
from project.core.log_config import get_logger
from project.main import app
from tests.utils.setup_db import (
    TEST_DB_URL,
    setup_db_before_tests,
    teardown_db_after_tests,
)

logger = get_logger(__name__)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Integrate anyio into pytest."""
    return "asyncio"


@pytest.fixture(scope="session")
async def db_engine_generator() -> AsyncGenerator[AsyncEngine, None]:
    """
    Manage the test database engine at the session level.

    1. Run custom setup method;
    2. Yields the SQLAlchemy test engine connected to the test database;
    3. Run custom teardown method.

    Returns:
        AsyncGenerator[AsyncEngine, None]: Main test engine.
    """
    test_engine: AsyncEngine | None = None
    try:
        await setup_db_before_tests()
        test_engine = create_async_engine(url=TEST_DB_URL)
        logger.info("Test engine created successfully.")
        yield test_engine

    except Exception as e:  # noqa
        logger.exception("Critical error during test database setup: %s", e)
        pytest.fail(f"Failed to configure test environment: {e}")
        if test_engine:
            await test_engine.dispose()

        logger.warning("Attempting cleanup after failed setup")
        try:
            await teardown_db_after_tests()
        except Exception as cleanup_e:  # noqa
            logger.error(
                "Error during cleanup after failed setup: %s", cleanup_e
            )
        raise  # исходная ошибка настройки, чтобы тесты не запустились

    finally:
        # очистка после всех тестов (выполняется после yield)
        logger.info("Starting final test environment cleanup")
        if test_engine:
            logger.info("Disposing test engine resources")
            await test_engine.dispose()
            logger.info("Test engine resources disposed")

        try:
            logger.info("Running final database teardown")
            await teardown_db_after_tests()
            logger.info("Final database teardown completed")
        except Exception:  # noqa
            logger.exception("Error during final teardown after tests")
            # не проваливаем сессию из-за ошибки очистки
            pass


@pytest.fixture(scope="function", autouse=True)
async def truncate_tables(
    db_engine_generator: AsyncEngine,
) -> AsyncGenerator[None, None]:
    """
    Clears all tables managed by Base.metadata before each test.
    Relies on transaction rollback in db_session for primary isolation.
    This provides an extra layer of safety.
    """
    logger.info("Start clearing tables (TRUNCATE) before test")
    table_names: list[str] = list(Base.metadata.tables.keys())

    if not table_names:
        logger.warning("No tables found in Base.metadata to truncate.")
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
        async with db_engine_generator.begin() as conn:
            logger.info("Run TRUNCATE on engine '%s'", db_engine_generator)
            await conn.execute(truncate_sql)
        logger.info("Tables truncated successfully.")

        yield  # выполнение теста

    except Exception as e:  # noqa
        logger.exception("Error during table truncation: %s", e)
        pytest.fail(f"Failed to truncate tables: {e}")


@pytest.fixture(scope="function")
async def db_session(
    db_engine_generator: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a test database session with automatic rollback via
    nested transactions.
    """
    async_session_maker = async_sessionmaker(
        bind=db_engine_generator,
        expire_on_commit=False,  # чтобы объекты были доступны после rollback
    )

    # создаем сессию из фабрики
    async with async_session_maker() as session:
        session_id = id(session)
        logger.debug("Test session '%s' created", session_id)
        # открываем вложенную транзакцию (SAVEPOINT)
        async with session.begin_nested():
            logger.debug(
                "Nested transaction (SAVEPOINT) started for session '%s'",
                session_id,
            )
            yield session  # отдаем сессию тесту
            # после yield неявный rollback SAVEPOINT
        logger.debug(
            "Nested transaction (SAVEPOINT) finished for session '%s'",
            session_id,
        )
    # основная транзакция сессии, если бы была, осталась бы нетронутой
    logger.debug("Test session '%s' closed", session_id)


@pytest.fixture(scope="function")
async def raw_db_session(
    db_engine_generator: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Provides a raw AsyncSession without automatic transaction management."""
    async_session_maker = async_sessionmaker(
        bind=db_engine_generator,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        session_id = id(session)
        logger.debug("Raw session '%s' created", session_id)
        try:
            yield session
        finally:
            logger.debug("Raw session '%s' closed", session_id)


@pytest.fixture(scope="function")
async def httpx_test_client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an HTTPX client for testing the FastAPI application."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
