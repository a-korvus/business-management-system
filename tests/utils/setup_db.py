"""
Setup test DB.

An independent engine is created to perform test environment setup.
"""

import asyncio
import logging
import os

from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

from project.app_auth.domain.models import Profile, User  # noqa
from project.app_org.domain.models import (  # noqa
    Command,
    Department,
    News,
    Role,
)
from project.config import settings
from project.core.db.base import Base

logger = logging.getLogger(__name__)

ADMIN_DB_URL = settings.DB.url_async
TEST_DB_NAME = os.getenv("PG_TEST_DB_NAME", "my_test_db")
TEST_DB_USER = os.getenv("PG_TEST_USER", "test_user")
TEST_DB_PASSWORD = os.getenv("PG_TEST_PASSWORD", "test_password")
TEST_DB_URL = (
    f"postgresql+asyncpg://{TEST_DB_USER}:{TEST_DB_PASSWORD}@"
    f"{settings.DB.HOST}:{settings.DB.PORT}/{TEST_DB_NAME}"
)


async def create_test_db_and_user(
    admin_connection_url: str,
    test_db: str,
    test_user: str,
    test_password: str,
) -> None:
    """
    Connect to PostgreSQL and create test db and test user.

    Use existing credentials. Dispose of the engine after completing work.
    """
    # движок от имени администратора для создания тестовой среды
    admin_engine = create_async_engine(
        admin_connection_url,
        isolation_level="AUTOCOMMIT",  # AUTOCOMMIT нужен для CREATE DATABASE
    )

    async with admin_engine.connect() as conn:
        try:
            # проверить/создать тестового пользователя
            user_exists = await conn.execute(
                text("SELECT 1 FROM pg_roles WHERE rolname = :user"),
                {"user": test_user},
            )
            if not user_exists.scalar_one_or_none():
                logger.info("Creating test user '%s'", test_user)
                # идентификаторы нельзя параметризовать :param
                create_user_sql = text(
                    f'CREATE USER "{test_user}" '
                    f"WITH PASSWORD '{test_password}'"
                )
                await conn.execute(create_user_sql)
                logger.info("User '%s' created", test_user)
            else:
                logger.info("Test user '%s' already exists", test_user)

            # проверить/создать тестовую базу данных
            db_exists = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": test_db},
            )
            if not db_exists.scalar_one_or_none():
                logger.info("Creating test DB '%s'", test_db)
                # Устанавливаем владельцем нового пользователя
                await conn.execute(
                    text(f'CREATE DATABASE "{test_db}" OWNER "{test_user}"')
                )
                logger.info("Database '%s' created", test_db)
            else:
                logger.info("Database '%s' already exists", test_db)

            # выдать права test_user на БД, даже если она уже есть
            # нужно, если БД была создана ранее другим способом
            logger.info("Grant privileges on '%s' to '%s'", test_db, test_user)
            await conn.execute(
                text(
                    f'GRANT ALL PRIVILEGES ON DATABASE "{test_db}" '
                    f'TO "{test_user}"'
                )
            )
            logger.info(
                "Privileges to '%s' on '%s' granted", test_user, test_db
            )
        except ProgrammingError as e:
            logger.exception(
                "SQL Programming error during test db/user setup: %s", e
            )
            raise RuntimeError(
                f"Failed to configure test DB/user due to SQL error: {e}"
            ) from e
        except DBAPIError as e:
            # ошибка подключения или другая ошибка DBAPI
            logger.exception("DBAPI error during test db/user setup: %s", e)
            # проверяем, является ли это ошибкой подключения
            if "connection refused" in str(e).lower() or isinstance(
                e.orig, OSError
            ):
                logger.error(
                    "Could not connect to the database. Ensure the PostgreSQL "
                    "server is running and accessible at '%s'.",
                    admin_connection_url.split("@")[-1],
                )
                raise RuntimeError(
                    "Failed to connect to admin DB. Is the server running?"
                ) from e
            else:
                raise RuntimeError(
                    "Failed to configure test DB/user due to DBAPI error"
                ) from e
        except Exception as e:
            logger.exception("Unexpected error while setting up test DB")
            raise RuntimeError("Failed to configure test DB/user") from e

    # закрываем движок после использования
    await admin_engine.dispose()
    logger.info("Admin setup engine disposed.")


async def setup_db_before_tests() -> None:
    """
    Run creating test DB and test user.

    Raises:
        RuntimeError: Exceptions raised during setup.
    """
    logger.info("Start setup_environment_for_tests")
    test_engine = None
    try:
        # создание БД и пользователя
        await create_test_db_and_user(
            admin_connection_url=ADMIN_DB_URL,
            test_db=TEST_DB_NAME,
            test_user=TEST_DB_USER,
            test_password=TEST_DB_PASSWORD,
        )
        logger.info("Test database and user setup complete.")
        logger.info("URL to connect to the test DB: '%s'", TEST_DB_URL)

        # создание таблиц в тестовой БД
        test_engine = create_async_engine(url=TEST_DB_URL)

        async with test_engine.begin() as conn:
            logger.info("Creating tables in the test DB '%s'.", TEST_DB_NAME)
            # запускаем синхронный create_all через run_sync
            # метод create_all работает с объектом MetaData,
            # поэтому остается синхронным
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables created successfully in the test DB.")

        logger.info(
            "The test environment setup has been completed successfully"
        )
        # тут можно вернуть движок дальше для фикстур сессии, если нужно
        # return test_engine
    except RuntimeError as e:
        logger.exception("Error setting up test environment: %s", e)
        raise
    finally:
        # очищаем ресурсы движка тестовой БД, если он был создан
        if test_engine:
            logger.info("Disposing of test engine used for table creation.")
            await test_engine.dispose()
            logger.info("Test engine disposed.")
        else:
            logger.warning("Test engine was not created, skipping disposal.")


async def cleanup_test_environment(
    admin_connection_url: str,
    test_db: str,
    test_user: str,
) -> None:
    """Cleanup all test environment."""
    logger.info(
        "Running test environment cleanup. Dropping DB: '%s', User: '%s'",
        test_db,
        test_user,
    )
    # создаем движок от админ пользователя, не тест
    admin_engine = create_async_engine(
        admin_connection_url,
        isolation_level="AUTOCOMMIT",  # AUTOCOMMIT нужен для DROP DATABASE
    )

    async with admin_engine.connect() as conn:
        try:
            logger.info("Terminating active sessions to DB '%s'", test_db)
            # завершить все активные подключения к БД, за исключением текущего
            # иначе невозможно удалить БД с актиынми подключениями
            terminate_sessions_sql = text(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity "
                "WHERE datname = :db_name AND pid <> pg_backend_pid()"
            )
            # может вернуть строки, если сессии были завершены
            terminated_result = await conn.execute(
                terminate_sessions_sql, {"db_name": test_db}
            )
            terminated_pids = terminated_result.fetchall()
            if terminated_pids:
                logger.info(
                    "Terminated %d active session(s) to DB '%s'",
                    len(terminated_pids),
                    test_db,
                )
            else:
                logger.info("No active sessions found for DB '%s'", test_db)

            # удалить тестовую базу данных
            logger.info("Dropping the test database '%s'", test_db)
            drop_db_sql = text(f'DROP DATABASE IF EXISTS "{test_db}"')
            await conn.execute(drop_db_sql)
            logger.info("Database '%s' dropped successfully", test_db)

            # удалить тестового пользователя
            logger.info("Dropping the test user '%s'", test_user)
            drop_user_sql = text(f'DROP USER IF EXISTS "{test_user}"')
            await conn.execute(drop_user_sql)
            logger.info("User '%s' dropped successfully", test_user)

        except ProgrammingError as e:
            # Ошибки 'database "..." does not exist' или
            # 'role "..." does not exist' могут быть при повторном запуске
            # очистки. Логируем как warning и пропускаем.
            logger.warning(
                "Ignoring SQL programming error during cleanup "
                "(likely object already dropped): %s",
                e,
            )
            pass
        except DBAPIError as e:
            logger.exception("DBAPI error during cleanup: %s", e)
            # Проверяем, является ли это ошибкой подключения
            if "connection refused" in str(e).lower() or isinstance(
                e.orig, OSError
            ):
                logger.error(
                    "Could not connect to the admin database for cleanup. "
                    "Ensure the PostgreSQL server is running and accessible "
                    "at '%s'.",
                    admin_connection_url.split("@")[-1],
                )
            raise RuntimeError("Cleanup failed due to DBAPI error") from e
        except Exception as e:
            logger.exception("Unexpected error during cleanup")
            raise RuntimeError("Cleanup failed due to unexpected error") from e

    await admin_engine.dispose()
    logger.info("Admin cleanup engine disposed.")


async def teardown_db_after_tests() -> None:
    """
    Call test environment cleanup.

    Raises:
        RuntimeError: Exception occurred while cleanup the test environment.
    """
    logger.info("Starting test environment cleanup after tests.")
    try:
        await cleanup_test_environment(
            admin_connection_url=ADMIN_DB_URL,
            test_db=TEST_DB_NAME,
            test_user=TEST_DB_USER,
        )
        logger.info("Test environment cleanup finished successfully.")
    except RuntimeError:
        logger.exception("Error while cleanup test environment")
        raise


async def main() -> None:
    """Run setup, simulate tests, and run teardown."""
    await setup_db_before_tests()
    print("\n>>> The test environment is set up, you can run tests <<<\n")
    # тут выполняются тесты
    input(">>> Press Enter to start cleaning the environment <<<\n")
    await teardown_db_after_tests()


if __name__ == "__main__":
    # export PROJECT_DEV_MODE=1
    # echo $PROJECT_DEV_MODE
    asyncio.run(main())
