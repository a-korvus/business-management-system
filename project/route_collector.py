"""Collecting routers from all applications in this project."""

from fastapi import APIRouter

from project.app_auth.presentation.routers.auth import router as rr_auth
from project.app_auth.presentation.routers.users import router as rr_users
from project.app_org.presentation.routers.commands import router as rr_commands
from project.app_org.presentation.routers.departments import (
    router as rr_departments,
)
from project.app_org.presentation.routers.news import router as rr_news
from project.app_org.presentation.routers.roles import router as rr_roles

project_routers: list[APIRouter] = [
    rr_auth,
    rr_users,
    rr_commands,
    rr_departments,
    rr_roles,
    rr_news,
]
