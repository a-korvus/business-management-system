"""Main project configuration file.

Uses pydantic BaseSettings to load environment variables.
Combines configurations for different parts of the project.
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR: Path = Path(__file__).resolve().parent.parent


class PGConfig(BaseSettings):
    """PostgreSQL connection configuration."""

    HOST: str = "localhost"
    PORT: int = 5432
    DB_NAME: str = "my_db"
    USER: str = "task_user"
    PASSWORD: str = "some_pswr"
    DSN: PostgresDsn | None = None

    # для админского движка в тестовом окружении
    ADMIN_DB_NAME: str = "my_db"
    ADMIN_USER: str = "task_user"
    ADMIN_PASSWORD: str = "some_pswr"

    model_config = SettingsConfigDict(env_prefix="PG_", extra="allow")

    @property
    def url_async(self) -> str:
        """Use for postgres connection with 'asyncpg' driver.

        In tests, data is pulled here to connect to the test database.
        example: postgresql+asyncpg://postgres:postgres@localhost:5432/db_name
        """
        if self.DSN:
            return str(self.DSN)

        return (
            "postgresql+asyncpg://"
            f"{self.USER}:{self.PASSWORD}@"
            f"{self.HOST}:{self.PORT}/{self.DB_NAME}"
        )

    @property
    def admin_url_async(self) -> str:
        """Use for admin postgres connection in tests."""
        return (
            "postgresql+asyncpg://"
            f"{self.ADMIN_USER}:{self.ADMIN_PASSWORD}@"
            f"{self.HOST}:{self.PORT}/{self.ADMIN_DB_NAME}"
        )


class RedisConfig(BaseSettings):
    """Redis config."""

    USER: str = "admin_user"
    USER_PASSWORD: str = "admin_user_password"
    HOST: str = "localhost"
    PORT: int = 6379
    DSN: RedisDsn | None = None

    CACHE_DB: int = 0
    CELERY_BROKER_DB: int = 1
    CELERY_BACKEND_DB: int = 2

    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="allow")

    def _create_url(self, db_num: int) -> str:
        """Create a link to redis connection.

        Args:
            host (str): Host to connection.
            db_num (int): Indicate the database number.

        Returns:
            str: URL to connection.
        """
        # redis://username:password@localhost:6379/0
        return (
            f"redis://{self.USER}:{self.USER_PASSWORD}@"
            f"{self.HOST}:{self.PORT}/{db_num}"
        )

    @property
    def url_cache(self) -> str:
        """Config a link to caching redis connection."""
        return self._create_url(db_num=self.CACHE_DB)

    @property
    def url_celery_broker(self) -> str:
        """Config a link to celery broker redis connection."""
        return self._create_url(db_num=self.CELERY_BROKER_DB)

    @property
    def url_celery_backend(self) -> str:
        """Config a link to celery backend redis connection."""
        return self._create_url(db_num=self.CELERY_BACKEND_DB)


class AuthConfig(BaseSettings):
    """Configuration specific to the 'app auth' application."""

    # префиксы роутеров
    PREFIX_AUTH: str = "/auth"
    PREFIX_USERS: str = "/users"

    # JWT settings
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_TYPE: str = "JWT"
    JWT_ISSUER: str = "my_auth_server"  # кто создал и подписал токен
    JWT_AUDIENCE: str = "my_api_resource"  # кто получает токен
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # настройки хеширования паролей (Argon2)
    ARGON2_TIME_COST: int = 3  # количество итераций при хэшировании
    ARGON2_MEMORY_COST: int = 65536  # 64 MiB опер.памяти на хэш одного пароля
    ARGON2_PARALLELISM: int = os.cpu_count() or 4
    ARGON2_SALT_LENGTH: int = 16  # byte, 128 bit
    ARGON2_HASH_LENGTH: int = 32  # byte, 256 bit

    model_config = SettingsConfigDict(env_prefix="AUTH_", extra="allow")


class ProjectSettings(BaseSettings):
    """Main project settings class.

    Combines all other configurations and common settings.
    Loads settings from environment variables.
    """

    DEV_MODE: bool = False
    LOG_DIR: Path = ROOT_DIR / "log"
    ADMIN_SECRET_KEY: str = ""
    MASTER_EMAIL: str = ""
    MASTER_PASSWORD: str = ""
    PREFIX_ORG: str = "/org"

    # вложенные конфиги
    DB: PGConfig = PGConfig()
    REDIS: RedisConfig = RedisConfig()
    AUTH: AuthConfig = AuthConfig()

    model_config = SettingsConfigDict(env_prefix="PROJECT_", extra="allow")


@lru_cache(maxsize=1)
def get_settings() -> ProjectSettings:
    """Cache the settings config."""
    return ProjectSettings()


settings: ProjectSettings = get_settings()
