"""MQTT Protocol Adapter component (ADR 4).
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..schemas.telemetry_schemas import TelemetryRequest

TOPIC_PATTERN = re.compile(r"^ozagrimate/farms/(?P<farmId>FARM-\d+)/devices/(?P<deviceId>DEV-\d+)/telemetry$")


class MqttProtocolAdapter:
    def to_telemetry_request(self, topic: str, payload: bytes) -> TelemetryRequest:
        match = TOPIC_PATTERN.match(topic)
        if not match:
            raise ValueError(f"Unrecognised MQTT topic: {topic}")
        message: dict[str, Any] = json.loads(payload.decode("utf-8"))
        # Vendor MQTT payloads use compact keys: id, ts, data=[{m, v, u}]
        return TelemetryRequest(
            eventId=message["id"],
            farmId=match["farmId"],
            deviceId=match["deviceId"],
            recordedAt=message["ts"],
            readings=[{"metric": r["m"], "value": r["v"], "unit": r["u"]} for r in message["data"]],
        )
