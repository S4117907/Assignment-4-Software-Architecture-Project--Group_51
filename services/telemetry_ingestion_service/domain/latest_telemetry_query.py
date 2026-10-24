"""Latest-telemetry query used by the dashboard (part of the Telemetry Repository read path).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shared.errors import not_found
from shared.security import GatewayClaims

from ..events.device_directory_cache import DeviceDirectoryCache
from ..repository.telemetry_repository import TelemetryRepository
from ..schemas.telemetry_schemas import Metric

STALE_AFTER_MINUTES = 10


class LatestTelemetryQuery:
    def __init__(self, repository: TelemetryRepository, directory: DeviceDirectoryCache):
        self._repository = repository
        self._directory = directory

    def latest(self, farm_id: str, claims: GatewayClaims, metric: Metric | None, zone_id: str | None) -> dict[str, Any]:
        if not self._directory.farm_exists(farm_id):
            raise not_found("FARM_NOT_FOUND", f"Farm {farm_id} was not found.")
        claims.require_farm_access(farm_id)

        now = datetime.now(timezone.utc)
        readings = []
        for r in self._repository.latest_for_farm(farm_id):
            if not self._directory.is_active(r["deviceId"]):
                continue  # decommissioned devices no longer appear on the dashboard
            if metric and r["metric"] != metric.value:
                continue
            if zone_id and r["zoneId"] != zone_id:
                continue
            age = (now - r["recordedAt"]).total_seconds() / 60
            readings.append({**r, "ageMinutes": round(age, 1), "stale": age > STALE_AFTER_MINUTES})
        return {
            "farmId": farm_id,
            "generatedAt": now,
            "staleAfterMinutes": STALE_AFTER_MINUTES,
            "readingCount": len(readings),
            "readings": readings,
        }
