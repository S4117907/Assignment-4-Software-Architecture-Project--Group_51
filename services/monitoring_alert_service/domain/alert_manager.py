"""Alert Manager component: creates, de-duplicates and lists alerts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.errors import not_found
from shared.observability import log_event
from shared.security import GatewayClaims

from ..consumers.farm_directory import FarmDirectory
from ..events.alert_event_publisher import SERVICE_NAME, AlertEventPublisher
from ..repository.alert_repository import AlertRepository
from ..schemas.alert_schemas import AlertStatus, Severity
from .threshold_rule_engine import ThresholdRuleEngine

CHANNELS_BY_SEVERITY = {"CRITICAL": ["SMS", "PUSH"], "WARNING": ["PUSH"]}


class AlertManager:
    def __init__(self, repository: AlertRepository, rules: ThresholdRuleEngine,
                 publisher: AlertEventPublisher, farms: FarmDirectory):
        self._repository = repository
        self._rules = rules
        self._publisher = publisher
        self._farms = farms

    def handle_telemetry_event(self, event: dict[str, Any]) -> None:
        payload = event["payload"]
        for reading in payload["readings"]:
            match = self._rules.evaluate(reading["metric"], reading["value"])
            if match is None:
                continue
            observed_at = datetime.fromisoformat(payload["recordedAt"])
            existing = self._repository.open_alert_for(payload["farmId"], payload["deviceId"], match.alert_type)
            if existing:
                # One open alert per device and condition: avoids alert storms from repeated readings.
                existing.update(observedValue=reading["value"], lastObservedAt=observed_at,
                                occurrenceCount=existing["occurrenceCount"] + 1)
                continue
            alert = self._repository.save({
                "alertId": self._repository.next_alert_id(),
                "farmId": payload["farmId"],
                "alertType": match.alert_type,
                "severity": match.severity,
                "status": "OPEN",
                "deviceId": payload["deviceId"],
                "zoneId": payload.get("zoneId"),
                "metric": reading["metric"],
                "observedValue": reading["value"],
                "unit": reading["unit"],
                "threshold": match.threshold,
                "message": (f"{reading['metric'].replace('_', ' ').title()} is {reading['value']} {reading['unit']}, "
                            f"{match.direction} the {match.severity.lower()} threshold of {match.threshold}."),
                "triggeredAt": observed_at,
                "lastObservedAt": observed_at,
                "occurrenceCount": 1,
                "sourceEventId": payload["eventId"],
                "notifications": [{"channel": c, "deliveryStatus": "QUEUED"}
                                  for c in CHANNELS_BY_SEVERITY[match.severity]],
            })
            self._publisher.alert_raised(alert)
            log_event(SERVICE_NAME, "alert.raised", alertId=alert["alertId"], farmId=alert["farmId"],
                      severity=alert["severity"])

    def list_alerts(self, farm_id: str, claims: GatewayClaims, status: AlertStatus | None,
                    severity: Severity | None, limit: int) -> dict[str, Any]:
        if not self._farms.exists(farm_id):
            raise not_found("FARM_NOT_FOUND", f"Farm {farm_id} was not found.")
        claims.require_farm_access(farm_id)
        alerts = [a for a in self._repository.for_farm(farm_id)
                  if (status is None or a["status"] == status.value)
                  and (severity is None or a["severity"] == severity.value)][:limit]
        return {
            "farmId": farm_id,
            "count": len(alerts),
            "filters": {"status": status, "severity": severity, "limit": limit},
            "alerts": alerts,
        }
