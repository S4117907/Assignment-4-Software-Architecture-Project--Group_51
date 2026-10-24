"""Telemetry Event Publisher component (ADR 2, ADR 6).
"""

from __future__ import annotations

from typing import Any

from shared.messaging import EventPublisher, topics

SERVICE_NAME = "telemetry-ingestion-service"


class TelemetryEventPublisher:
    def __init__(self) -> None:
        self._publisher = EventPublisher(producer=SERVICE_NAME)

    def telemetry_received(self, payload: dict[str, Any]) -> str:
        self._publisher.publish(topics.TELEMETRY_RECEIVED, payload["farmId"], "TelemetryReceived", payload)
        return topics.TELEMETRY_RECEIVED
