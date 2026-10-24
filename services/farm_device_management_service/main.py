"""Farm and Device Management Service - container entry point.

"""

from fastapi import FastAPI

from shared.errors import install_error_handlers
from shared.observability import install_observability

from .api import device_router, farm_router

SERVICE_NAME = "farm-device-management-service"

app = FastAPI(
    title="OzAgriMate - Farm and Device Management Service",
    version="1.0.0",
    description="Manages farms, irrigation zones and the device registry. Part of the OzAgriMate open API v1.",
)
install_observability(app, SERVICE_NAME)
install_error_handlers(app)
app.include_router(farm_router.router)
app.include_router(device_router.router)
