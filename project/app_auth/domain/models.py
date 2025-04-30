"""Domain SQLAlchemy models in the 'app_auth' app."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import UUID as UUID_SQL
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from project.app_org.domain.models import Role
from project.core.db.base import Base

if TYPE_CHECKING:
    from project.app_auth.application.interfaces import PasswordHasher


class User(Base):
    """Main User in project. Each user can have only one profile."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_SQL(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT", name="fk_users_role_id"),
        nullable=True,
        index=True,
        default=None,
    )

    profile: Mapped[Profile] = relationship(
        "Profile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="joined",
    )
    role: Mapped[Role | None] = relationship(
        back_populates="users",
    )

    def __init__(
        self,
        email: str,
        plain_password: str,
        hasher: "PasswordHasher",
        **kwargs: Any,
    ) -> None:
        """Initialize the user.

        Handles standard attribute assignments via super(), then performs
        custom logic for email validation, password hashing,
        and profile creation.
        """
        super().__init__(**kwargs)

        if not email:
            raise ValueError("Email cannot be empty.")

        self.email = email
        self.set_password(plain_password, hasher)

        if not hasattr(self, "profile") or self.profile is None:
            self.profile = Profile()

    def set_password(
        self,
        plain_password: str,
        hasher: "PasswordHasher",
    ) -> None:
        """Hash and set password."""
        if not plain_password:
            raise ValueError("Password cannot be empty.")
        self.hashed_password = hasher.hash_password(plain_password)

    def check_password(
        self,
        plain_password: str,
        hasher: "PasswordHasher",
    ) -> bool:
        """Check the entered password matches the saved hash."""
        if not plain_password or not self.hashed_password:
            return False

        return hasher.verify_password(plain_password, self.hashed_password)

    def activate(self) -> None:
        """Activate the user."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate the user."""
        self.is_active = False

    def update_email(self, new_email: str) -> None:
        """Update user email."""
        # сюда можно добавить доп.проверки, валидацию на уровне БД и т.д.
        if not new_email:
            raise ValueError("New email cannot be empty.")
        self.email = new_email


class Profile(Base):
    """User profile. Each profile can only belong to one user."""

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_SQL(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    first_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", name="fk_profiles_user_id"),
        unique=True,
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="profile")

    def update_profile(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        bio: str | None = None,
    ) -> None:
        """Update the profile fields content."""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if bio is not None:
            self.bio = bio
