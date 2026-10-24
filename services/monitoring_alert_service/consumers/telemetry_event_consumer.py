"""Telemetry Event Consumer component.

"""

from __future__ import annotations

from shared.messaging import EventConsumer, topics

from ..domain.alert_manager import AlertManager

CONSUMER_GROUP = "monitoring-alert-service"


class TelemetryEventConsumer:
    def __init__(self, manager: AlertManager):
        self._manager = manager
        self._consumer = EventConsumer(topics.TELEMETRY_RECEIVED, CONSUMER_GROUP)

    def drain(self) -> int:
        events = self._consumer.poll()
        for event in events:
            if event.get("eventType") == "TelemetryReceived":
                self._manager.handle_telemetry_event(event)
        return len(events)
