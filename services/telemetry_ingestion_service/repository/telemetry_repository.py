"""Telemetry Repository component.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from shared.dev_seed import seed


class TelemetryRepository:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._readings: list[dict[str, Any]] = []
        self._latest: dict[tuple[str, str], dict[str, Any]] = {}
        self._quarantine: list[dict[str, Any]] = []
        self._load_seed()

    def _load_seed(self) -> None:
        """Recent readings so GET latest has data; DEV-1005 is deliberately stale (38 min)."""
        now = datetime.now(timezone.utc)
        zones = {d["deviceId"]: d["zoneId"] for d in seed("devices")}
        samples = [
            ("FARM-001", "DEV-1001", "SOIL_MOISTURE", 27.4, "PERCENT", 4),
            ("FARM-001", "DEV-1001", "SOIL_TEMPERATURE", 16.8, "CELSIUS", 4),
            ("FARM-001", "DEV-1002", "AIR_TEMPERATURE", 24.1, "CELSIUS", 2),
            ("FARM-001", "DEV-1002", "RELATIVE_HUMIDITY", 48.0, "PERCENT", 2),
            ("FARM-001", "DEV-1004", "WATER_FLOW_RATE", 0.0, "LITRES_PER_MINUTE", 3),
            ("FARM-001", "DEV-1005", "SOIL_MOISTURE", 31.2, "PERCENT", 38),
            ("FARM-002", "DEV-2001", "SOIL_MOISTURE", 22.0, "PERCENT", 6),
        ]
        for farm_id, device_id, metric, value, unit, minutes_ago in samples:
            recorded = now - timedelta(minutes=minutes_ago)
            self.store_reading({
                "farmId": farm_id, "deviceId": device_id, "zoneId": zones.get(device_id),
                "metric": metric, "value": value, "unit": unit,
                "recordedAt": recorded, "receivedAt": recorded + timedelta(seconds=2),
                "sourceEventId": f"SEED-{device_id}-{metric}",
            })

    def store_reading(self, reading: dict[str, Any]) -> None:
        with self._lock:
            self._readings.append(reading)
            key = (reading["deviceId"], reading["metric"])
            current = self._latest.get(key)
            # Late (buffered) data must never overwrite a newer reading (ASR9).
            if current is None or reading["recordedAt"] >= current["recordedAt"]:
                self._latest[key] = reading

    def quarantine(self, record: dict[str, Any]) -> None:
        with self._lock:
            self._quarantine.append(record)

    def latest_for_farm(self, farm_id: str) -> list[dict[str, Any]]:
        return sorted(
            (r for r in self._latest.values() if r["farmId"] == farm_id),
            key=lambda r: (r["deviceId"], r["metric"]),
        )

    @property
    def quarantined(self) -> list[dict[str, Any]]:
        return list(self._quarantine)
