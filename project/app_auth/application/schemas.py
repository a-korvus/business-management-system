"""Validation schemas for domain models in the 'app_auth'."""

from pydantic import BaseModel


class UserSchemaInput(BaseModel):
    """Schema to validate the user input data."""
