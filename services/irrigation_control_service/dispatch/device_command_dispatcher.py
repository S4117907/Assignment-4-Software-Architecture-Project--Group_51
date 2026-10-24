"""Device Command Dispatcher component (ADR 4). 
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from shared.messaging import EventPublisher

SERVICE_NAME = "irrigation-control-service"
ACK_TIMEOUT = timedelta(seconds=5)
LOCAL_HUB_TOPIC = "iot-device-hub.commands"


class DeviceCommandDispatcher:
    def __init__(self) -> None:
        self._hub = EventPublisher(producer=SERVICE_NAME)

    def dispatch(self, command: dict[str, Any], actuator: dict[str, Any], now: datetime) -> dict[str, Any]:
        mqtt_topic = f"ozagrimate/farms/{command['farmId']}/zones/{command['zoneId']}/commands"
        self._hub.publish(LOCAL_HUB_TOPIC, command["farmId"], "IrrigationCommandIssued", {
            "mqttTopic": mqtt_topic,
            "qos": 1,
            "commandId": command["commandId"],
            "targetDeviceId": actuator["deviceId"],
            "action": command["action"],
            "durationMinutes": command["durationMinutes"],
            "flowRateLitresPerMinute": command["flowRateLitresPerMinute"],
        })
        return {
            "targetDeviceId": actuator["deviceId"],
            "protocol": "MQTT",
            "topic": mqtt_topic,
            "qos": 1,
            "acknowledgementDeadline": now + ACK_TIMEOUT,
        }
