"""Alert API Router component: exposes farm alerts to the Web and Mobile Application (API v1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query

from shared.security import GatewayClaims, gateway_claims

from ..consumers.telemetry_event_consumer import TelemetryEventConsumer
from ..dependencies import alert_manager, telemetry_consumer
from ..domain.alert_manager import AlertManager
from ..schemas.alert_schemas import AlertListResponse, AlertStatus, Severity

router = APIRouter(prefix="/api/v1/farms/{farmId}/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse, summary="Retrieve farm alerts")
def list_alerts(
    farmId: str = Path(pattern=r"^FARM-\d{3,6}$"),
    status: AlertStatus | None = Query(default=None),
    severity: Severity | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    claims: GatewayClaims = Depends(gateway_claims),
    manager: AlertManager = Depends(alert_manager),
    consumer: TelemetryEventConsumer = Depends(telemetry_consumer),
) -> dict:
    """Endpoint 6 - GET /api/v1/farms/{farmId}/alerts?status=OPEN&severity=CRITICAL&limit=20."""
    consumer.drain()
    return manager.list_alerts(farmId, claims, status, severity, limit)
