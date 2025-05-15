"""SQLAdmin ModelView definitions for 'app_org' models."""

from sqladmin import ModelView

from project.app_org.domain.models import Command, Department, News, Role


class CommandAdmin(ModelView, model=Command):
    """Command admin model."""

    category = "Organization"


class DepartmentAdmin(ModelView, model=Department):
    """Department admin model."""

    category = "Organization"


class RoleAdmin(ModelView, model=Role):
    """Role admin model."""

    category = "Organization"


class NewsAdmin(ModelView, model=News):
    """News admin model."""

    category = "Organization"
