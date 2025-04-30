"""Project logger config."""

import logging
import logging.config
import sys
from functools import lru_cache

from project.config import settings

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
            "filename": f"{settings.LOG_DIR}/log.log",
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
if settings.DEV_MODE:
    # log_conf["loggers"]["file"]["level"] = "DEBUG"
    # log_conf["handlers"]["file"]["level"] = "DEBUG"
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


@lru_cache(maxsize=128)
def get_logger(name: str) -> logging.Logger:
    """Create configured logger.

    Args:
        name (str): Set a name for a new logger.

    Returns:
        logging.Logger: New configured logger.
    """
    logger = logging.getLogger(name)
    logging.config.dictConfig(log_conf)

    return logger
