"""SQLAlchemy Base project model."""

from sqlalchemy.exc import MissingGreenlet
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from project.core.log_config import get_logger

logger = get_logger(__name__)


class Base(AsyncAttrs, DeclarativeBase):
    """Base model for all project sqlalchemy models."""

    __abstract__ = True

    _repr_cols_num: int = 1
    _repr_cols: tuple = ()

    def __repr__(self) -> str:
        """Display the Model string representation."""
        cols = []

        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self._repr_cols or idx < self._repr_cols_num:
                try:
                    col_value = getattr(self, col)
                except MissingGreenlet:
                    logger.exception("Impossible to perform column '%s'", col)
                    col_value = "<unloaded>"

                cols.append(f"{col}={col_value}")

        return f"<{self.__class__.__name__}: {', '.join(cols)}>"
