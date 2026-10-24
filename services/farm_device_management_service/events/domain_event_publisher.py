"""Domain Event Publisher component.

Publishes farm and device lifecycle events to the Message Broker (ADR 6) so other
services (Telemetry Ingestion, Monitoring and Alert, Irrigation Control) can keep
their local reference data current without calling this service synchronously.
Events are keyed by farmId, which selects the broker partition (ADR 2).
"""

from __future__ import annotations

from typing import Any

from shared.messaging import EventPublisher, topics

SERVICE_NAME = "farm-device-management-service"


class DomainEventPublisher:
    def __init__(self) -> None:
        self._publisher = EventPublisher(producer=SERVICE_NAME)

    def farm_registered(self, farm: dict[str, Any]) -> None:
        self._publisher.publish(topics.FARM_EVENTS, farm["farmId"], "FarmRegistered", _farm_payload(farm))

    def farm_updated(self, farm: dict[str, Any]) -> None:
        self._publisher.publish(topics.FARM_EVENTS, farm["farmId"], "FarmUpdated", _farm_payload(farm))

    def device_decommissioned(self, device: dict[str, Any]) -> None:
        self._publisher.publish(
            topics.DEVICE_EVENTS,
            device["farmId"],
            "DeviceDecommissioned",
            {
                "deviceId": device["deviceId"],
                "farmId": device["farmId"],
                "deviceType": device["deviceType"],
                "zoneId": device.get("zoneId"),
            },
        )


def _farm_payload(farm: dict[str, Any]) -> dict[str, Any]:
    return {
        "farmId": farm["farmId"],
        "name": farm["name"],
        "ownerUserId": farm["ownerUserId"],
        "timezone": farm["timezone"],
        "irrigationZones": farm["irrigationZones"],
        "version": farm["version"],
    }
