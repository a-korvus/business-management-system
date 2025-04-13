"""The main entrypoint to FastAPI app."""

from fastapi import APIRouter, FastAPI
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)

routers: list[APIRouter] = []


@app.get("/health/", status_code=200, tags=["health check"])
async def health_check() -> dict:
    """
    Use it endpoint to health check.

    Returns:
        dict: {"status": "ok"} if the service is running.
    """
    return {"status": "ok"}


for router in routers:
    app.include_router(router)
