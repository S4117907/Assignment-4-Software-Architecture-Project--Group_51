"""Telemetry Validator component.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from shared.errors import not_found, unprocessable

from ..events.device_directory_cache import DeviceDirectoryCache
from ..schemas.telemetry_schemas import Metric, NormalisedReading

PLAUSIBLE_RANGES: dict[Metric, tuple[float, float]] = {
    Metric.SOIL_MOISTURE: (0.0, 100.0),
    Metric.SOIL_TEMPERATURE: (-20.0, 70.0),
    Metric.AIR_TEMPERATURE: (-30.0, 60.0),
    Metric.RELATIVE_HUMIDITY: (0.0, 100.0),
    Metric.RAINFALL: (0.0, 500.0),
    Metric.WIND_SPEED: (0.0, 250.0),
    Metric.WATER_FLOW_RATE: (0.0, 5000.0),
}

METRICS_BY_DEVICE_TYPE: dict[str, set[Metric]] = {
    "SOIL_MOISTURE_SENSOR": {Metric.SOIL_MOISTURE, Metric.SOIL_TEMPERATURE},
    "WEATHER_STATION": {Metric.AIR_TEMPERATURE, Metric.RELATIVE_HUMIDITY, Metric.RAINFALL, Metric.WIND_SPEED},
    "FLOW_METER": {Metric.WATER_FLOW_RATE},
    "IRRIGATION_VALVE_CONTROLLER": {Metric.WATER_FLOW_RATE},
}

MAX_CLOCK_SKEW = timedelta(minutes=5)


class TelemetryValidationError(Exception):
    """Raised for readings that must be quarantined (wraps the API error to return)."""

    def __init__(self, api_error):
        super().__init__(api_error.message)
        self.api_error = api_error


class TelemetryValidator:
    def __init__(self, directory: DeviceDirectoryCache):
        self._directory = directory

    def resolve_device(self, farm_id: str, device_id: str) -> dict[str, Any]:
        if not self._directory.farm_exists(farm_id):
            raise not_found("FARM_NOT_FOUND", f"Farm {farm_id} was not found.")
        device = self._directory.active_device(farm_id, device_id)
        if device is None:
            raise not_found(
                "DEVICE_NOT_REGISTERED",
                f"Device {device_id} is not an active registered device of farm {farm_id}.",
            )
        return device

    def validate(self, device: dict[str, Any], recorded_at: datetime, received_at: datetime,
                 readings: list[NormalisedReading]) -> None:
        if recorded_at - received_at > MAX_CLOCK_SKEW:
            raise TelemetryValidationError(unprocessable(
                "TIMESTAMP_IN_FUTURE", "recordedAt is more than 5 minutes ahead of the platform clock.",
                [{"field": "recordedAt"}]))

        allowed = METRICS_BY_DEVICE_TYPE.get(device["deviceType"], set())
        problems = []
        for index, reading in enumerate(readings):
            if reading.metric not in allowed:
                problems.append({"field": f"readings.{index}.metric",
                                 "issue": f"{reading.metric.value} is not produced by a {device['deviceType']}"})
                continue
            low, high = PLAUSIBLE_RANGES[reading.metric]
            if not low <= reading.value <= high:
                problems.append({"field": f"readings.{index}.value",
                                 "issue": f"{reading.value} {reading.unit} is outside the plausible range {low}-{high}"})
        if problems:
            raise TelemetryValidationError(unprocessable(
                "READING_REJECTED", "One or more readings failed validation and were quarantined.", problems))
