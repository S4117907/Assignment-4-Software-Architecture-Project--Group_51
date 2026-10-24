"""
Persists farms, irrigation zones and devices. In production this maps to the
``farm_device`` schema of the Operational Database (PostgreSQL, ADR 7); in this
prototype it is an in-memory dictionary seeded from the dummy reference data.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

from shared.dev_seed import seed


def _now() -> datetime:
    return datetime.now(timezone.utc)


class FarmDeviceRepository:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._farms: dict[str, dict[str, Any]] = {}
        self._devices: dict[str, dict[str, Any]] = {}
        self._next_farm_number = 1
        self._load_seed()

    def _load_seed(self) -> None:
        created = _now()
        for farm in seed("farms"):
            farm.update(status="ACTIVE", version=1, createdAt=created, updatedAt=created)
            self._farms[farm["farmId"]] = farm
            self._next_farm_number = max(self._next_farm_number, int(farm["farmId"].split("-")[1]) + 1)
        for device in seed("devices"):
            device["status"] = "ACTIVE"
            self._devices[device["deviceId"]] = device

    # farms
    def next_farm_id(self) -> str:
        with self._lock:
            farm_id = f"FARM-{self._next_farm_number:03d}"
            self._next_farm_number += 1
            return farm_id

    def get_farm(self, farm_id: str) -> dict[str, Any] | None:
        return self._farms.get(farm_id)

    def find_farm_by_pic(self, pic: str) -> dict[str, Any] | None:
        return next((f for f in self._farms.values() if f["propertyIdentificationCode"] == pic), None)

    def save_farm(self, farm: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._farms[farm["farmId"]] = farm
        return farm

    # devices 
    def devices_for_farm(self, farm_id: str) -> list[dict[str, Any]]:
        return [d for d in self._devices.values() if d["farmId"] == farm_id and d["status"] == "ACTIVE"]

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        return self._devices.get(device_id)

    def save_device(self, device: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._devices[device["deviceId"]] = device
        return device
