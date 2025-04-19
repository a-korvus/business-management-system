"""
Main project configuration file.

Uses pydantic BaseSettings to load environment variables.
Combines configurations for different parts of the project.
"""

import os
from pathlib import Path

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR: Path = Path(__file__).resolve().parent.parent


class PGConfig(BaseSettings):
    """PostgreSQL connection configuration."""

    HOST: str = "localhost"
    PORT: int = 5432
    DB_NAME: str = "mydb"
    USER: str = "user"
    PASSWORD: str = "password"

    DSN: PostgresDsn | None = None

    model_config = SettingsConfigDict(env_prefix="PG_", extra="allow")

    @property
    def url_async(self) -> str:
        """
        Config a link to postgres connection for asyncpg.

        example: postgresql+asyncpg://postgres:postgres@localhost:5432/db_name
        """
        if self.DSN:
            return str(self.DSN)

        return (
            "postgresql+asyncpg://"
            f"{self.USER}:{self.PASSWORD}@"
            f"{self.HOST}:{self.PORT}/{self.DB_NAME}"
        )


class AuthConfig(BaseSettings):
    """Configuration specific to the 'app auth' application."""

    # префиксы роутеров
    PREFIX_AUTH: str = "/auth"
    PREFIX_USERS: str = "/users"

    # JWT settings
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # настройки хеширования паролей (Argon2)
    ARGON2_TIME_COST: int = 3  # количество итераций при хэшировании
    ARGON2_MEMORY_COST: int = 65536  # 64 MiB опер.памяти на хэш одного пароля
    ARGON2_PARALLELISM: int = os.cpu_count() or 4
    ARGON2_SALT_LENGTH: int = 16  # byte, 128 bit
    ARGON2_HASH_LENGTH: int = 32  # byte, 256 bit

    model_config = SettingsConfigDict(env_prefix="AUTH_", extra="allow")


class ProjectSettings(BaseSettings):
    """
    Main project settings class.

    Combines all other configurations and common settings.
    Loads settings from environment variables.
    """

    DEV_MODE: bool = False
    LOG_DIR: Path = ROOT_DIR / "log"

    # вложенные конфиги
    DB: PGConfig = PGConfig()
    AUTH: AuthConfig = AuthConfig()

    model_config = SettingsConfigDict(env_prefix="PROJECT_", extra="allow")


settings = ProjectSettings()
