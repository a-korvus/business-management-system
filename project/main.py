"""The main FastAPI project entrypoint."""

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from project.core.log_config import get_logger
from project.route_collector import project_routers

logger = get_logger(__name__)

app = FastAPI(default_response_class=ORJSONResponse)


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

logger.debug(msg=f"Registered routers: {len(project_routers)}")
