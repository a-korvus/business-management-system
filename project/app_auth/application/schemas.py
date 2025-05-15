"""Validation schemas for domain models in the 'app_auth'."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from project.app_org.application.schemas import CommandRead, RoleRead


class UserBase(BaseModel):
    """Pre-configured user base model."""

    email: EmailStr


class UserCreate(UserBase):
    """Schema to validate the entered new user data."""

    password: str = Field(..., min_length=8)
    command_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None


class UserRead(UserBase):
    """Schema to serialize the User instance."""

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    command_id: uuid.UUID | None
    role_id: uuid.UUID | None

    profile: ProfileRead

    model_config = ConfigDict(from_attributes=True)


class UserDetail(UserBase):
    """Schema to serialize the User instance with all related data."""

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    command_id: uuid.UUID | None
    role_id: uuid.UUID | None

    profile: ProfileRead
    command: CommandRead | None
    role: RoleRead | None

    model_config = ConfigDict(from_attributes=True)


class ProfileBase(BaseModel):
    """Pre-configured Profile base model."""

    first_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=255)


class ProfileCreate(ProfileBase):
    """Schema to validate the entered new profile data."""

    ...


class ProfileUpdate(ProfileBase):
    """Schema to validate the entered existing profile data to update it."""

    ...


class ProfileRead(ProfileBase):
    """Schema to serialize the existing profile data."""

    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class LoginSchema(BaseModel):
    """Schema to validate the credentials."""

    username: EmailStr  # в качестве логина используем email пользователя
    password: str


class Token(BaseModel):
    """Schema to validate the entered auth token."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema to validate inner JWT token data."""

    sub: EmailStr | None = None  # (subject) для email по стандарту JWT
    uid: str | None = None
