"""Project database configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class PGConfig(BaseSettings):
    """Postgres configuration."""

    PG_HOST: str = "localhost"
    PG_PORT: int = 5432
    PG_DB_NAME: str = "mydb"
    PG_USER: str = "user"
    PG_PASSWORD: str = "password"

    model_config = SettingsConfigDict(extra="allow")

    @property
    def url_async(self) -> str:
        """Config a link to postgres connection for asyncpg."""
        # postgresql+asyncpg://postgres:postgres@localhost:5432/db_name
        return (
            "postgresql+asyncpg://"
            f"{self.PG_USER}:{self.PG_PASSWORD}@"
            f"{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB_NAME}"
        )


db_config = PGConfig()
