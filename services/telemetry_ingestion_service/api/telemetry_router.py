"""Telemetry API Router component: HTTPS ingestion and dashboard read endpoints (API v1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query, Response, status

from shared.security import GatewayClaims, gateway_claims

from ..dependencies import ingestion_pipeline, latest_query
from ..domain.ingestion_pipeline import IngestionPipeline
from ..domain.latest_telemetry_query import LatestTelemetryQuery
from ..schemas.telemetry_schemas import LatestTelemetryResponse, Metric, TelemetryAccepted, TelemetryDuplicate, TelemetryRequest

router = APIRouter(prefix="/api/v1", tags=["Telemetry"])


@router.post(
    "/telemetry",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TelemetryAccepted | TelemetryDuplicate,
    summary="Submit sensor telemetry",
    responses={200: {"model": TelemetryDuplicate, "description": "Duplicate eventId - ignored (idempotent)"}},
)
def submit_telemetry(
    body: TelemetryRequest,
    response: Response,
    claims: GatewayClaims = Depends(gateway_claims),
    pipeline: IngestionPipeline = Depends(ingestion_pipeline),
) -> dict:
    """Endpoint 4 - POST /api/v1/telemetry. 202 Accepted: stored and published for asynchronous processing."""
    accepted, result = pipeline.ingest(body, claims)
    if not accepted:
        response.status_code = status.HTTP_200_OK
    return result


@router.get(
    "/farms/{farmId}/telemetry/latest",
    response_model=LatestTelemetryResponse,
    summary="Retrieve latest telemetry",
)
def latest_telemetry(
    farmId: str = Path(pattern=r"^FARM-\d{3,6}$"),
    metric: Metric | None = Query(default=None, description="Filter by canonical metric"),
    zoneId: str | None = Query(default=None, pattern=r"^ZONE-[A-Z0-9]{1,6}$"),
    claims: GatewayClaims = Depends(gateway_claims),
    query: LatestTelemetryQuery = Depends(latest_query),
) -> dict:
    """Endpoint 5 - GET /api/v1/farms/{farmId}/telemetry/latest. Latest value per device and metric."""
    return query.latest(farmId, claims, metric, zoneId)
