"""Validation schemas for domain models in the 'app_auth'."""

from __future__ import annotations

import uuid
from datetime import datetime

from project.app_org.application.schemas import RoleRead

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TunedModel(BaseModel):
    """Pre-configured pydantic base model."""

    model_config = ConfigDict(from_attributes=True)


class UserBase(TunedModel):
    """Pre-configured user base model."""

    email: EmailStr


class UserCreate(UserBase):
    """Schema to validate the entered new user data."""

    password: str = Field(..., min_length=8)
    role_id: uuid.UUID | None = None
    profile: ProfileCreate | None = None


class UserRead(UserBase):
    """Schema to serialize the existing user data."""

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    profile: ProfileRead | None
    role: RoleRead | None


# class UserUpdate(TunedModel):
#     """Schema to validate the entered existing user data to update it."""

#     email: EmailStr | None = None
#     password: str | None = Field(None, max_length=8)
#     is_active: bool | None = None
#     profile: ProfileUpdate | None = None


class ProfileBase(TunedModel):
    """Pre-configured Profile base model."""

    first_name: str | None = Field(None, max_length=50)
    last_name: str | None = Field(None, max_length=50)
    bio: str | None = Field(None, max_length=255)


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
