"""Configuration for the 'app_auth' app."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthConfig(BaseSettings):
    """Secret values to use in 'app_auth'."""

    APP_AUTH_PREFIX_AUTH: str = "/auth"
    APP_AUTH_PREFIX_USERS: str = "/users"

    # JWT settings
    SECRET_KEY: str = "load_from_env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # cryptography settings
    ARGON2_TIME_COST: int = 3  # количество итераций при хэшировании
    ARGON2_MEMORY_COST: int = 65536  # 64 MiB опер.памяти на хэш одного пароля
    ARGON2_PARALLELISM: int = os.cpu_count() or 4
    ARGON2_SALT_LENGTH: int = 16  # byte, 128 bit
    ARGON2_HASH_LENGTH: int = 32  # byte, 256 bit

    model_config = SettingsConfigDict(extra="allow")


auth_config = AuthConfig()
