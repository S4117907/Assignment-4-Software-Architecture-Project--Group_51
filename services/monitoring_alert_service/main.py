"""Monitoring and Alert Service - container entry point.

Run from the repository root:
    uvicorn services.monitoring_alert_service.main:app --port 8003
"""

from fastapi import FastAPI

from shared.errors import install_error_handlers
from shared.observability import install_observability

from .api import alert_router

SERVICE_NAME = "monitoring-alert-service"

app = FastAPI(
    title="OzAgriMate - Monitoring and Alert Service",
    version="1.0.0",
    description="Consumes TelemetryReceived events, evaluates threshold rules and manages farm alerts. "
                "Part of the OzAgriMate open API v1.",
)
install_observability(app, SERVICE_NAME)
install_error_handlers(app)
app.include_router(alert_router.router)
