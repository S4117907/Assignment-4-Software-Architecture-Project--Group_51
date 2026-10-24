"""Telemetry Ingestion Pipeline component.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from shared.errors import ApiError
from shared.observability import log_event
from shared.security import GatewayClaims, Role

from ..adapters.payload_normaliser import PayloadNormaliser
from ..events.telemetry_event_publisher import SERVICE_NAME, TelemetryEventPublisher
from ..repository.telemetry_repository import TelemetryRepository
from ..schemas.telemetry_schemas import TelemetryRequest
from .deduplication_filter import DeduplicationFilter
from .telemetry_validator import TelemetryValidationError, TelemetryValidator

LATE_ARRIVAL_AFTER = timedelta(minutes=10)
INGEST_ROLES = (Role.DEVICE_GATEWAY, Role.OPERATIONS_SUPPORT)


class IngestionPipeline:
    def __init__(self, normaliser: PayloadNormaliser, validator: TelemetryValidator,
                 dedup: DeduplicationFilter, repository: TelemetryRepository, publisher: TelemetryEventPublisher):
        self._normaliser = normaliser
        self._validator = validator
        self._dedup = dedup
        self._repository = repository
        self._publisher = publisher

    def ingest(self, request: TelemetryRequest, claims: GatewayClaims) -> tuple[bool, dict[str, Any]]:
        """Returns (accepted, body). accepted=False means an idempotent duplicate."""
        claims.require_role(*INGEST_ROLES)
        claims.require_farm_access(request.farmId)

        first_seen = self._dedup.first_seen(request.eventId)
        if first_seen is not None:
            return False, {
                "eventId": request.eventId,
                "status": "DUPLICATE_IGNORED",
                "firstReceivedAt": first_seen,
                "message": "This event was already ingested; it was not stored or published again.",
            }

        device = self._validator.resolve_device(request.farmId, request.deviceId)
        received_at = datetime.now(timezone.utc)
        recorded_at = request.recordedAt.astimezone(timezone.utc)

        try:
            readings = self._normaliser.normalise(request.readings)
            self._validator.validate(device, recorded_at, received_at, readings)
        except (TelemetryValidationError, ApiError) as exc:
            api_error = exc.api_error if isinstance(exc, TelemetryValidationError) else exc
            self._repository.quarantine({"request": request.model_dump(mode="json"), "reason": api_error.code,
                                         "details": api_error.details, "receivedAt": received_at})
            log_event(SERVICE_NAME, "telemetry.quarantined", eventId=request.eventId, reason=api_error.code)
            raise api_error from None

        late = received_at - recorded_at > LATE_ARRIVAL_AFTER
        for reading in readings:
            self._repository.store_reading({
                "farmId": request.farmId, "deviceId": request.deviceId, "zoneId": device.get("zoneId"),
                "metric": reading.metric.value, "value": reading.value, "unit": reading.unit,
                "recordedAt": recorded_at, "receivedAt": received_at, "sourceEventId": request.eventId,
            })
        self._dedup.remember(request.eventId, received_at)

        body = {
            "eventId": request.eventId,
            "status": "ACCEPTED",
            "farmId": request.farmId,
            "deviceId": request.deviceId,
            "zoneId": device.get("zoneId"),
            "recordedAt": recorded_at,
            "receivedAt": received_at,
            "lateArrival": late,
            "readings": [r.model_dump(mode="json") for r in readings],
        }
        body["publishedTo"] = self._publisher.telemetry_received({**body, "deviceType": device["deviceType"]})
        return True, body
