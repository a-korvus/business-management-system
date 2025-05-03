"""Collecting routers from all applications in this project."""

from fastapi import APIRouter

from project.app_auth.presentation.routers.auth import router as rr_auth
from project.app_auth.presentation.routers.users import router as rr_users
from project.app_org.presentation.routers.news import router as rr_news

project_routers: list[APIRouter] = [rr_auth, rr_users, rr_news]
