"""SQLAdmin ModelView definitions for 'app_auth' models."""

from markupsafe import Markup
from sqladmin import ModelView

from project.app_admin.formatters import format_datetime_local
from project.app_auth.domain.models import Profile, User


class UserAdmin(ModelView, model=User):
    """User admin model."""

    column_list = [
        User.email,
        User.is_active,
        User.created_at,
        User.updated_at,
    ]
    column_export_exclude_list = [User.hashed_password]
    column_formatters = {
        User.created_at: format_datetime_local,
        User.updated_at: format_datetime_local,
    }
    column_searchable_list = [User.email]
    column_sortable_list = [User.created_at, User.updated_at]
    column_default_sort = "created_at"

    column_details_list = [
        User.email,
        User.created_at,
        User.updated_at,
        User.is_active,
        User.profile,
        User.role,
    ]
    column_formatters_detail = {
        User.created_at: format_datetime_local,
        User.updated_at: format_datetime_local,
        User.profile: lambda m, a: Markup("<b>Go to profile</b>"),
        User.role: lambda m, a: Markup("<b>Go to role</b>"),
    }

    form_excluded_columns = [User.hashed_password, User.profile]

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


class ProfileAdmin(ModelView, model=Profile):
    """Profile admin model."""

    column_list = [
        Profile.first_name,
        Profile.last_name,
    ]
    column_export_exclude_list = [Profile.id]
    column_sortable_list = [Profile.last_name, Profile.first_name]
    column_searchable_list = [Profile.first_name, Profile.last_name]

    column_details_list = [
        Profile.first_name,
        Profile.last_name,
        Profile.bio,
        Profile.user,
    ]
    form_columns = [
        Profile.first_name,
        Profile.last_name,
        Profile.bio,
    ]
    column_formatters_detail = {
        Profile.user: lambda m, a: Markup("<b>Go to user</b>"),
    }

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True

    page_size = 20
    page_size_options = [10, 25, 50, 100, 200]

    category = "Accounts"
    name = "Profile"
    name_plural = "Profiles"
    icon = "fa-solid fa-circle-user"
