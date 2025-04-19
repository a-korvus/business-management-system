"""The main FastAPI project entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from project.core.db.setup import async_engine
from project.core.log_config import get_logger
from project.route_collector import project_routers

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Application startup.")
    yield
    logger.info("Application shutdown.")
    await async_engine.dispose()
    logger.info("Database connection closed.")


app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    title="Business management system.",
    description="Microservice app. Business vanagement and control system",
)


@app.get("/health/", status_code=200, tags=["health check"])
async def health_check() -> dict:
    """
    Use it endpoint to health check.

    Returns:
        dict: {"status": "ok"} if the service is running.
    """
    return {"status": "ok"}


for app_router in project_routers:
    app.include_router(app_router)

logger.debug("Registered routers: %d", len(project_routers))
