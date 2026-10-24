"""Telemetry Ingestion Service - container entry point.

Run from the repository root:
    uvicorn services.telemetry_ingestion_service.main:app --port 8002
"""

from fastapi import FastAPI

from shared.errors import install_error_handlers
from shared.observability import install_observability

from .api import telemetry_router

SERVICE_NAME = "telemetry-ingestion-service"

app = FastAPI(
    title="OzAgriMate - Telemetry Ingestion Service",
    version="1.0.0",
    description="Receives, normalises, validates, deduplicates and stores device telemetry, then publishes "
                "TelemetryReceived events. Part of the OzAgriMate open API v1.",
)
install_observability(app, SERVICE_NAME)
install_error_handlers(app)
app.include_router(telemetry_router.router)
