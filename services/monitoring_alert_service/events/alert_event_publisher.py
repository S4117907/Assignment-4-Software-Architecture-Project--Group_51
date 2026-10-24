"""Alert Event Publisher component.
"""

from __future__ import annotations

from typing import Any

from shared.messaging import EventPublisher, topics

SERVICE_NAME = "monitoring-alert-service"


class AlertEventPublisher:
    def __init__(self) -> None:
        self._publisher = EventPublisher(producer=SERVICE_NAME)

    def alert_raised(self, alert: dict[str, Any]) -> None:
        payload = {k: alert[k] for k in ("alertId", "farmId", "alertType", "severity", "deviceId", "zoneId",
                                          "message", "notifications")}
        self._publisher.publish(topics.ALERT_RAISED, alert["farmId"], "AlertRaised", payload)
