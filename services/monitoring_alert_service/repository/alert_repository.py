"""Alert Repository component.

Stores alerts in the ``monitoring`` schema of the Operational Database (ADR 7).
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any


class AlertRepository:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._alerts: dict[str, dict[str, Any]] = {}
        self._next_number = 1
        self._load_seed()

    def _load_seed(self) -> None:
        now = datetime.now(timezone.utc)
        seeds = [
            ("FARM-001", "LOW_SOIL_MOISTURE", "WARNING", "RESOLVED", "DEV-1005", "ZONE-B", "SOIL_MOISTURE",
             18.6, "PERCENT", 20.0, now - timedelta(days=2), [("PUSH", "DELIVERED")]),
            ("FARM-001", "POSSIBLE_PIPE_BURST", "CRITICAL", "ACKNOWLEDGED", "DEV-1004", "ZONE-A", "WATER_FLOW_RATE",
             512.0, "LITRES_PER_MINUTE", 400.0, now - timedelta(hours=5), [("SMS", "DELIVERED"), ("PUSH", "DELIVERED")]),
            ("FARM-002", "LOW_SOIL_MOISTURE", "WARNING", "OPEN", "DEV-2001", "ZONE-A", "SOIL_MOISTURE",
             17.9, "PERCENT", 20.0, now - timedelta(hours=1), [("PUSH", "DELIVERED")]),
        ]
        for farm, a_type, sev, status, device, zone, metric, value, unit, threshold, at, notes in seeds:
            self.save({
                "alertId": self.next_alert_id(), "farmId": farm, "alertType": a_type, "severity": sev,
                "status": status, "deviceId": device, "zoneId": zone, "metric": metric,
                "observedValue": value, "unit": unit, "threshold": threshold,
                "message": f"{metric.replace('_', ' ').title()} {value} {unit} breached threshold {threshold}.",
                "triggeredAt": at, "lastObservedAt": at, "occurrenceCount": 1,
                "sourceEventId": f"SEED-{device}",
                "notifications": [{"channel": c, "deliveryStatus": s} for c, s in notes],
            })

    def next_alert_id(self) -> str:
        with self._lock:
            alert_id = f"ALT-{self._next_number:04d}"
            self._next_number += 1
            return alert_id

    def save(self, alert: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._alerts[alert["alertId"]] = alert
        return alert

    def open_alert_for(self, farm_id: str, device_id: str, alert_type: str) -> dict[str, Any] | None:
        return next((a for a in self._alerts.values()
                     if a["farmId"] == farm_id and a["deviceId"] == device_id
                     and a["alertType"] == alert_type and a["status"] == "OPEN"), None)

    def for_farm(self, farm_id: str) -> list[dict[str, Any]]:
        return sorted((a for a in self._alerts.values() if a["farmId"] == farm_id),
                      key=lambda a: a["lastObservedAt"], reverse=True)
