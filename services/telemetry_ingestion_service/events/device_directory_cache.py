"""Device Directory Cache component.
"""

from __future__ import annotations

from typing import Any

from shared.dev_seed import seed
from shared.messaging import EventConsumer, topics

CONSUMER_GROUP = "telemetry-ingestion-service"


class DeviceDirectoryCache:
    def __init__(self) -> None:
        self._farms: set[str] = {farm["farmId"] for farm in seed("farms")}
        self._devices: dict[str, dict[str, Any]] = {d["deviceId"]: {**d, "status": "ACTIVE"} for d in seed("devices")}
        self._farm_consumer = EventConsumer(topics.FARM_EVENTS, CONSUMER_GROUP)
        self._device_consumer = EventConsumer(topics.DEVICE_EVENTS, CONSUMER_GROUP)

    def refresh(self) -> None:
        for event in self._farm_consumer.poll():
            if event["eventType"] == "FarmRegistered":
                self._farms.add(event["payload"]["farmId"])
        for event in self._device_consumer.poll():
            if event["eventType"] == "DeviceDecommissioned":
                device = self._devices.get(event["payload"]["deviceId"])
                if device:
                    device["status"] = "DECOMMISSIONED"

    def farm_exists(self, farm_id: str) -> bool:
        self.refresh()
        return farm_id in self._farms

    def active_device(self, farm_id: str, device_id: str) -> dict[str, Any] | None:
        self.refresh()
        device = self._devices.get(device_id)
        if device and device["farmId"] == farm_id and device["status"] == "ACTIVE":
            return device
        return None

    def is_active(self, device_id: str) -> bool:
        device = self._devices.get(device_id)
        return bool(device and device["status"] == "ACTIVE")
