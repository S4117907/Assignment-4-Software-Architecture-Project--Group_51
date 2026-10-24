"""Request and response contracts for the Telemetry Ingestion Service (API v1)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Metric(str, Enum):
    SOIL_MOISTURE = "SOIL_MOISTURE"
    SOIL_TEMPERATURE = "SOIL_TEMPERATURE"
    AIR_TEMPERATURE = "AIR_TEMPERATURE"
    RELATIVE_HUMIDITY = "RELATIVE_HUMIDITY"
    RAINFALL = "RAINFALL"
    WIND_SPEED = "WIND_SPEED"
    WATER_FLOW_RATE = "WATER_FLOW_RATE"


class ReadingIn(BaseModel):
    """A raw reading as sent by a device; units may be vendor-specific."""

    model_config = ConfigDict(extra="forbid")

    metric: str = Field(min_length=2, max_length=40)
    value: float
    unit: str = Field(min_length=1, max_length=30)


class TelemetryRequest(BaseModel):
    """Body for POST /api/v1/telemetry."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "eventId": "EVT-1001-000123",
                "farmId": "FARM-001",
                "deviceId": "DEV-1001",
                "recordedAt": "2026-10-14T09:15:00+11:00",
                "readings": [
                    {"metric": "SOIL_MOISTURE", "value": 0.142, "unit": "FRACTION"},
                    {"metric": "SOIL_TEMPERATURE", "value": 64.4, "unit": "FAHRENHEIT"},
                ],
            }
        },
    )

    eventId: str = Field(pattern=r"^[A-Za-z0-9\-]{6,64}$", description="Device-side unique ID used for deduplication")
    farmId: str = Field(pattern=r"^FARM-\d{3,6}$")
    deviceId: str = Field(pattern=r"^DEV-\d{3,6}$")
    recordedAt: AwareDatetime = Field(description="Original device timestamp (ISO 8601 with offset)")
    readings: list[ReadingIn] = Field(min_length=1, max_length=50)


class NormalisedReading(BaseModel):
    metric: Metric
    value: float
    unit: str


class TelemetryAccepted(BaseModel):
    eventId: str
    status: str
    farmId: str
    deviceId: str
    zoneId: str | None
    recordedAt: datetime
    receivedAt: datetime
    lateArrival: bool
    readings: list[NormalisedReading]
    publishedTo: str


class TelemetryDuplicate(BaseModel):
    eventId: str
    status: str
    firstReceivedAt: datetime
    message: str


class LatestReading(BaseModel):
    deviceId: str
    zoneId: str | None
    metric: Metric
    value: float
    unit: str
    recordedAt: datetime
    receivedAt: datetime
    ageMinutes: float
    stale: bool


class LatestTelemetryResponse(BaseModel):
    farmId: str
    generatedAt: datetime
    staleAfterMinutes: int
    readingCount: int
    readings: list[LatestReading]
