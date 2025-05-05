"""Validation schemas for domain models in the 'app_org'."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

from project.app_org.application.enums import RoleType


class CommandBase(BaseModel):
    """Command base schema."""

    description: str | None = Field(default=None, max_length=500)


class CommandCreate(CommandBase):
    """Validate the command input data."""

    name: str = Field(..., max_length=100)


class CommandUpdate(CommandBase):
    """Update existing command."""

    name: str | None = Field(default=None, max_length=100)


class CommandRead(CommandBase):
    """Schema to serialize the existing command data."""

    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentBase(BaseModel):
    """Department base schema."""

    description: str | None = Field(default=None, max_length=500)
    command_id: uuid.UUID | None = None


class DepartmentCreate(DepartmentBase):
    """Validate the department input data."""

    name: str = Field(..., max_length=100)


class DepartmentUpdate(DepartmentBase):
    """Update existing department."""

    name: str | None = Field(default=None, max_length=100)


class DepartmentRead(DepartmentBase):
    """Schema to serialize the existing department data."""

    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime
    command_id: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    """Role base schema."""

    description: str | None = Field(default=None, max_length=500)
    department_id: uuid.UUID | None = None


class RoleCreate(RoleBase):
    """Validate the role input data."""

    name: RoleType | None = RoleType.WORKER

    @field_validator("name", mode="before")
    @classmethod
    def ensure_name_lower(cls, value: str | None) -> str | None:
        """Ensure the 'name' value is lowercase."""
        if value is not None and not isinstance(value, str):
            raise ValidationError(f"Role name {value} isn't a string")

        if isinstance(value, str):
            value = value.lower()

        return value


class RoleUpdate(RoleBase):
    """Update existing role."""

    name: RoleType | None = None

    @field_validator("name", mode="before")
    @classmethod
    def ensure_name_lower(cls, value: str | None) -> str | None:
        """Ensure the 'name' value is lowercase."""
        if value is not None and not isinstance(value, str):
            raise ValidationError(f"Role name {value} isn't a string")

        if isinstance(value, str):
            value = value.lower()

        return value


class RoleRead(RoleBase):
    """Schema to serialize the existing role data."""

    id: uuid.UUID
    name: RoleType
    created_at: datetime
    updated_at: datetime
    department_id: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)


class NewsBase(BaseModel):
    """News base schema."""

    text: str = Field(..., max_length=5000)


class NewsCreate(NewsBase):
    """Validate the input data."""

    ...


class NewsUpdate(NewsBase):
    """Update existing news."""

    ...


class NewsRead(NewsBase):
    """Schema to serialize the existing news data."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
