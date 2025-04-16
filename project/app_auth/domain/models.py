"""SQLAlchemy models in the 'app_auth' app."""

from project.core.db.base import Base


class User(Base):
    """Main User in project."""

    __tablename__ = "users"


class Profile(Base):
    """User profile."""

    __tablename__ = "profiles"
