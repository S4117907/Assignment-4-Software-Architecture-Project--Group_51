"""Unit tests for architecture tactics that are not exposed as endpoints (ADR 3, ADR 4)."""

import json

import pytest

from services.external_integration_service.resilience.circuit_breaker import CircuitBreaker
from services.telemetry_ingestion_service.adapters.mqtt_protocol_adapter import MqttProtocolAdapter
from services.telemetry_ingestion_service.adapters.payload_normaliser import PayloadNormaliser
from shared.errors import ApiError


def test_mqtt_adapter_maps_vendor_payload_to_canonical_request():
    payload = json.dumps({"id": "EVT-MQTT-0001", "ts": "2026-10-14T09:15:00+11:00",
                          "data": [{"m": "VWC", "v": 0.21, "u": "FRACTION"}]}).encode()
    request = MqttProtocolAdapter().to_telemetry_request("ozagrimate/farms/FARM-001/devices/DEV-1001/telemetry", payload)
    assert (request.farmId, request.deviceId) == ("FARM-001", "DEV-1001")
    reading = PayloadNormaliser().normalise(request.readings)[0]
    assert (reading.metric.value, reading.value, reading.unit) == ("SOIL_MOISTURE", 21.0, "PERCENT")


def test_normaliser_rejects_unconvertible_unit():
    request = MqttProtocolAdapter().to_telemetry_request(
        "ozagrimate/farms/FARM-001/devices/DEV-1001/telemetry",
        json.dumps({"id": "EVT-MQTT-0002", "ts": "2026-10-14T09:15:00+11:00",
                    "data": [{"m": "SOIL_MOISTURE", "v": 3, "u": "BUCKETS"}]}).encode())
    with pytest.raises(ApiError) as err:
        PayloadNormaliser().normalise(request.readings)
    assert err.value.code == "UNSUPPORTED_UNIT"


def test_circuit_breaker_opens_returns_fallback_then_recovers():
    now = [0.0]
    breaker = CircuitBreaker("weather-provider", failure_threshold=2, reset_timeout=30, clock=lambda: now[0])

    def failing():
        raise TimeoutError("provider down")

    assert breaker.call(failing, lambda: "cached") == "cached"
    assert breaker.call(failing, lambda: "cached") == "cached"
    assert breaker.state == CircuitBreaker.OPEN
    assert breaker.call(lambda: "live", lambda: "cached") == "cached"  # short-circuited
    now[0] = 31.0
    assert breaker.state == CircuitBreaker.HALF_OPEN
    assert breaker.call(lambda: "live", lambda: "cached") == "live"
    assert breaker.state == CircuitBreaker.CLOSED
