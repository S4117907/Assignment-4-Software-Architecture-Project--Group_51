"""Zone and Actuator Directory component.
"""

from __future__ import annotations

from typing import Any

from shared.dev_seed import seed
from shared.messaging import EventConsumer, topics

CONSUMER_GROUP = "irrigation-control-service"
ACTUATOR_TYPE = "IRRIGATION_VALVE_CONTROLLER"


class ZoneActuatorDirectory:
    def __init__(self) -> None:
        self._zones: dict[str, set[str]] = {f["farmId"]: {z["zoneId"] for z in f["irrigationZones"]} for f in seed("farms")}
        self._actuators: dict[str, dict[str, Any]] = {
            d["deviceId"]: {**d, "status": "ACTIVE"} for d in seed("devices") if d["deviceType"] == ACTUATOR_TYPE
        }
        self._farm_consumer = EventConsumer(topics.FARM_EVENTS, CONSUMER_GROUP)
        self._device_consumer = EventConsumer(topics.DEVICE_EVENTS, CONSUMER_GROUP)

    def refresh(self) -> None:
        for event in self._farm_consumer.poll():
            if event["eventType"] in ("FarmRegistered", "FarmUpdated"):
                payload = event["payload"]
                self._zones[payload["farmId"]] = {z["zoneId"] for z in payload["irrigationZones"]}
        for event in self._device_consumer.poll():
            if event["eventType"] == "DeviceDecommissioned" and event["payload"]["deviceId"] in self._actuators:
                self._actuators[event["payload"]["deviceId"]]["status"] = "DECOMMISSIONED"

    def farm_exists(self, farm_id: str) -> bool:
        self.refresh()
        return farm_id in self._zones

    def zone_exists(self, farm_id: str, zone_id: str) -> bool:
        return zone_id in self._zones.get(farm_id, set())

    def actuator_for(self, farm_id: str, zone_id: str) -> dict[str, Any] | None:
        return next((a for a in self._actuators.values()
                     if a["farmId"] == farm_id and a["zoneId"] == zone_id and a["status"] == "ACTIVE"), None)
