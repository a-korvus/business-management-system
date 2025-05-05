"""Domain SQLAlchemy models in the 'app_org' app."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID as UUID_SQL
from sqlalchemy import (
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from project.app_org.application.enums import RoleType
from project.core.db.base import Base

if TYPE_CHECKING:
    from project.app_auth.domain.models import User


class Command(Base):
    """Command in the organizational structure."""

    __tablename__ = "commands"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_SQL(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    users: Mapped[list[Department]] = relationship(
        "User",
        back_populates="command",
        cascade="save-update, merge",
    )
    departments: Mapped[list[Department]] = relationship(
        "Department",
        back_populates="command",
        cascade="save-update, merge",
    )


class Department(Base):
    """Department in command."""

    __tablename__ = "departments"
    _repr_cols = ("name",)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_SQL(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=False,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    command_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "commands.id",
            ondelete="RESTRICT",
            name="fk_departments_command_id",
        ),
        nullable=True,
        index=True,
        default=None,
    )

    command: Mapped[Command] = relationship(
        back_populates="departments",
    )
    roles: Mapped[list[Role]] = relationship(
        "Role",
        back_populates="department",
        cascade="save-update, merge",
    )


class Role(Base):
    """User role in department."""

    __tablename__ = "roles"
    _pg_enum_role_name = "role_type_enum"
    _repr_cols = ("name",)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_SQL(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[RoleType] = mapped_column(
        SQLEnum(
            RoleType,
            name=_pg_enum_role_name,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=RoleType.WORKER,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "departments.id",
            ondelete="RESTRICT",
            name="fk_roles_department_id",
        ),
        nullable=True,
        index=True,
        default=None,
    )

    department: Mapped[Department] = relationship(
        back_populates="roles",
    )
    users: Mapped[list[User]] = relationship(
        "User",
        back_populates="role",
        cascade="save-update, merge",
    )


class News(Base):
    """News in the system."""

    __tablename__ = "news"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_SQL(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    text: Mapped[str] = mapped_column(
        String(5000),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
