"""Payload Normaliser component (ADR 4 - protocol adapters and canonical telemetry model).
"""

from __future__ import annotations

from typing import Callable

from shared.errors import unprocessable

from ..schemas.telemetry_schemas import Metric, NormalisedReading, ReadingIn

CANONICAL_UNITS: dict[Metric, str] = {
    Metric.SOIL_MOISTURE: "PERCENT",
    Metric.SOIL_TEMPERATURE: "CELSIUS",
    Metric.AIR_TEMPERATURE: "CELSIUS",
    Metric.RELATIVE_HUMIDITY: "PERCENT",
    Metric.RAINFALL: "MILLIMETRES",
    Metric.WIND_SPEED: "KILOMETRES_PER_HOUR",
    Metric.WATER_FLOW_RATE: "LITRES_PER_MINUTE",
}

# Vendor metric names seen in the field -> canonical metric.
METRIC_ALIASES: dict[str, Metric] = {
    "SOIL_MOISTURE": Metric.SOIL_MOISTURE, "SM": Metric.SOIL_MOISTURE, "VWC": Metric.SOIL_MOISTURE,
    "SOIL_TEMPERATURE": Metric.SOIL_TEMPERATURE, "SOIL_TEMP": Metric.SOIL_TEMPERATURE,
    "AIR_TEMPERATURE": Metric.AIR_TEMPERATURE, "AIR_TEMP": Metric.AIR_TEMPERATURE, "TEMP": Metric.AIR_TEMPERATURE,
    "RELATIVE_HUMIDITY": Metric.RELATIVE_HUMIDITY, "RH": Metric.RELATIVE_HUMIDITY,
    "RAINFALL": Metric.RAINFALL, "RAIN": Metric.RAINFALL,
    "WIND_SPEED": Metric.WIND_SPEED,
    "WATER_FLOW_RATE": Metric.WATER_FLOW_RATE, "FLOW": Metric.WATER_FLOW_RATE,
}

# (source unit, canonical unit) -> conversion function
CONVERSIONS: dict[tuple[str, str], Callable[[float], float]] = {
    ("FRACTION", "PERCENT"): lambda v: v * 100.0,
    ("FAHRENHEIT", "CELSIUS"): lambda v: (v - 32.0) * 5.0 / 9.0,
    ("INCHES", "MILLIMETRES"): lambda v: v * 25.4,
    ("METRES_PER_SECOND", "KILOMETRES_PER_HOUR"): lambda v: v * 3.6,
    ("GALLONS_PER_MINUTE", "LITRES_PER_MINUTE"): lambda v: v * 3.78541,
}

UNIT_ALIASES = {"%": "PERCENT", "C": "CELSIUS", "°C": "CELSIUS", "F": "FAHRENHEIT", "°F": "FAHRENHEIT",
                "MM": "MILLIMETRES", "KMH": "KILOMETRES_PER_HOUR", "LPM": "LITRES_PER_MINUTE"}


class PayloadNormaliser:
    def normalise(self, readings: list[ReadingIn]) -> list[NormalisedReading]:
        return [self._normalise_one(index, reading) for index, reading in enumerate(readings)]

    def _normalise_one(self, index: int, reading: ReadingIn) -> NormalisedReading:
        metric = METRIC_ALIASES.get(reading.metric.strip().upper())
        if metric is None:
            raise unprocessable(
                "UNSUPPORTED_METRIC",
                f"Metric '{reading.metric}' is not supported by the canonical telemetry model.",
                [{"field": f"readings.{index}.metric", "supported": [m.value for m in Metric]}],
            )
        unit = reading.unit.strip().upper()
        unit = UNIT_ALIASES.get(unit, unit)
        canonical = CANONICAL_UNITS[metric]
        if unit == canonical:
            value = reading.value
        elif (unit, canonical) in CONVERSIONS:
            value = CONVERSIONS[(unit, canonical)](reading.value)
        else:
            raise unprocessable(
                "UNSUPPORTED_UNIT",
                f"Unit '{reading.unit}' cannot be converted to {canonical} for {metric.value}.",
                [{"field": f"readings.{index}.unit"}],
            )
        return NormalisedReading(metric=metric, value=round(value, 2), unit=canonical)
