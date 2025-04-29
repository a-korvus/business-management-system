"""Main FastAPI entrypoint for the Admin Panel."""

from sqladmin import ModelView

from project.app_admin.models.app_auth import ProfileAdmin, UserAdmin
from project.app_admin.models.app_org import (
    CommandAdmin,
    DepartmentAdmin,
    RoleAdmin,
    NewsAdmin,
)

admin_models: list[type[ModelView]] = [
    UserAdmin,
    ProfileAdmin,
    CommandAdmin,
    DepartmentAdmin,
    RoleAdmin,
    NewsAdmin,
]
