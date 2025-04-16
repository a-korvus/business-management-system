"""Collecting routers from all applications in this project."""

from fastapi import APIRouter

from project.app_auth.presentation.routers.auth import router as auth_router

project_routers: list[APIRouter] = [auth_router]
