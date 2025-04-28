"""SQLAdmin ModelView definitions for 'app_auth' models."""

from sqladmin import ModelView

from project.app_auth.domain.models import User


class UserAdmin(ModelView, model=User):
    column_list = [
        User.email,
        User.is_active,
        User.created_at,
        User.updated_at,
    ]
    column_searchable_list = [User.email]
    column_sortable_list = [User.created_at, User.updated_at]
    column_export_exclude_list = [User.id, User.hashed_password]
    column_default_sort = "created_at"

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True

    page_size = 20
    page_size_options = [10, 25, 50, 100, 200]

    category = "Accounts"
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
