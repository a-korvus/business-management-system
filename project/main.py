"""The main FastAPI project entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from sqladmin import Admin
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from project.app_admin.admin_collector import admin_models
from project.app_admin.auth_back import authentication_backend
from project.config import settings
from project.core.db.setup import async_engine
from project.core.exc_handlers import exc_handlers
from project.core.log_config import get_logger
from project.route_collector import project_routers

logger = get_logger(__name__)

middlewares = [
    Middleware(SessionMiddleware, secret_key=settings.ADMIN_SECRET_KEY),
]


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Implementation of FastAPI app life cycle."""
    logger.info("Application startup.")

    yield

    logger.info("Application shutdown.")
    await async_engine.dispose()
    logger.info("Database connection closed.")


app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    middleware=middlewares,
    title="Business management system.",
    description="Microservice app. Business management and control system",
)

for exc, handler in exc_handlers.items():
    app.add_exception_handler(exc, handler)

app_admin = Admin(
    app=app,
    engine=async_engine,
    title="BMS Admin Panel",
    authentication_backend=authentication_backend,
)


@app.get("/health/", status_code=200, tags=["health check"])
async def health_check() -> dict:
    """Use it endpoint to health check.

    Returns:
        dict: {"status": "ok"} if the service is running.
    """
    return {"status": "ok"}


for app_router in project_routers:
    app.include_router(app_router)

for admin_model in admin_models:
    app_admin.add_view(admin_model)

logger.debug("Registered exception handlers: %d", len(exc_handlers))
logger.debug("Registered routers: %d", len(project_routers))
logger.debug("Registered admin models: %d", len(admin_models))
