"""Main FastAPI entrypoint for the Admin Panel."""

from sqladmin import ModelView

from project.app_admin.models.app_auth import UserAdmin

admin_models: list[type[ModelView]] = [UserAdmin]
