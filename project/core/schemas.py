"""Validation schemas in the project."""

from pydantic import BaseModel, Field

from project.core import constants as CS


class Pagination(BaseModel):
    """Pagination options schema."""

    offset: int = 0
    limit: int = Field(default=CS.PAGE_SIZE_DEFAULT, le=CS.PAGE_SIZE_MAX)
