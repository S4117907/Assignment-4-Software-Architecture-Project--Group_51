"""Irrigation Control Service - container entry point.

Run from the repository root:
    uvicorn services.irrigation_control_service.main:app --port 8004
"""

from fastapi import FastAPI

from shared.errors import install_error_handlers
from shared.observability import install_observability

from .api import irrigation_command_router

SERVICE_NAME = "irrigation-control-service"

app = FastAPI(
    title="OzAgriMate - Irrigation Control Service",
    version="1.0.0",
    description="Validates, authorises, audits and dispatches irrigation commands to farm gateways. "
                "Part of the OzAgriMate open API v1.",
)
install_observability(app, SERVICE_NAME)
install_error_handlers(app)
app.include_router(irrigation_command_router.router)
