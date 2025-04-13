"""Project config data."""

import logging
import logging.config
import sys
from os import getenv
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR: Path = Path(__file__).resolve().parent.parent

ENV_FILE_PATH: Path = PROJECT_DIR / ".env"
LOG_DIR_PATH: Path = PROJECT_DIR / "log"

if find_dotenv(filename=str(ENV_FILE_PATH)):
    load_dotenv(dotenv_path=ENV_FILE_PATH)
else:
    sys.exit("Environment file not found")

# установка мода для разработки или продакшн
DEV_MODE: bool = getenv("DEV_MODE", "0") == "1"

# основная конфигурация логгера для проекта
log_conf: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "main": {
            "format": "[%(asctime)s.%(msecs)02d] %(funcName)10s "
            "%(module)s:%(lineno)d %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "filename": "log/log.log",
            "maxBytes": 1024 * 1024,  # 1 MB
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "main",
        },
    },
    "loggers": {
        "file": {
            "level": "INFO",
            "handlers": ["file"],
        },
        "root": {
            "level": "INFO",
            "handlers": ["file"],
        },
    },
}

# вспомогательная конфигурация логгера для development mode
if DEV_MODE:
    log_conf["handlers"]["console"] = {
        "class": "logging.StreamHandler",
        "level": "DEBUG",
        "formatter": "main",
        "stream": sys.stdout,
    }
    log_conf["loggers"]["console"] = {
        "level": "DEBUG",
        "handlers": ["console"],
    }
    log_conf["loggers"]["root"]["level"] = "DEBUG"
    log_conf["loggers"]["root"]["handlers"].append("console")


def get_logger(name: str) -> logging.Logger:
    """
    Create configured logger.

    Args:
        name (str): Set a name for a new logger.

    Returns:
        logging.Logger: New configured logger.
    """
    logger = logging.getLogger(name)
    logging.config.dictConfig(log_conf)

    return logger


class PGConfig(BaseSettings):
    """Postgres config."""

    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, extra="allow")

    PG_HOST: str = "localhost"
    PG_PORT: int = 5432
    PG_DB_NAME: str = "mydb"
    PG_USER: str = "user"
    PG_PASSWORD: str = "password"

    @property
    def url_async(self) -> str:
        """Config a link to postgres connection for asyncpg."""
        # postgresql+asyncpg://postgres:postgres@localhost:5432/db_name
        return (
            "postgresql+asyncpg://"
            f"{self.PG_USER}:{self.PG_PASSWORD}@"
            f"{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB_NAME}"
        )


pg_config = PGConfig()

LOG_DIR_PATH.mkdir(exist_ok=True)
