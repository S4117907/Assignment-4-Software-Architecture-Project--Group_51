"""Request and response contracts for the Farm and Device Management Service (API v1)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AustralianState(str, Enum):
    NSW = "NSW"
    VIC = "VIC"
    QLD = "QLD"
    WA = "WA"
    SA = "SA"
    TAS = "TAS"
    NT = "NT"
    ACT = "ACT"


class FarmType(str, Enum):
    HORTICULTURE = "HORTICULTURE"
    BROADACRE_CROPPING = "BROADACRE_CROPPING"
    COTTON = "COTTON"
    DAIRY = "DAIRY"
    LIVESTOCK = "LIVESTOCK"
    VITICULTURE = "VITICULTURE"
    MIXED = "MIXED"


class Location(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: AustralianState
    region: str = Field(min_length=2, max_length=80)
    # Bounding box of mainland Australia and Tasmania.
    latitude: float = Field(ge=-44.0, le=-10.0)
    longitude: float = Field(ge=112.0, le=154.0)


class IrrigationZone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zoneId: str = Field(pattern=r"^ZONE-[A-Z0-9]{1,6}$")
    name: str = Field(min_length=2, max_length=60)
    areaHectares: float = Field(gt=0)
    cropType: str = Field(min_length=2, max_length=60)


class FarmRequest(BaseModel):
    """Body for POST /api/v1/farms and PUT /api/v1/farms/{farmId} (full replacement)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Wattle Creek Vineyard",
                "propertyIdentificationCode": "SA123456",
                "farmType": "VITICULTURE",
                "location": {"state": "SA", "region": "Barossa Valley", "latitude": -34.5333, "longitude": 138.95},
                "areaHectares": 64.0,
                "timezone": "Australia/Adelaide",
                "irrigationZones": [
                    {"zoneId": "ZONE-A", "name": "Shiraz Block", "areaHectares": 30.0, "cropType": "Shiraz grapes"}
                ],
            }
        },
    )

    name: str = Field(min_length=3, max_length=100)
    propertyIdentificationCode: str = Field(
        pattern=r"^[A-Z0-9]{8}$",
        description="Australian Property Identification Code (PIC); unique per farm.",
    )
    farmType: FarmType
    location: Location
    areaHectares: float = Field(gt=0, le=1_000_000)
    timezone: str = Field(pattern=r"^Australia/[A-Za-z_]+$")
    irrigationZones: list[IrrigationZone] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def _zones_are_consistent(self) -> "FarmRequest":
        zone_ids = [zone.zoneId for zone in self.irrigationZones]
        if len(zone_ids) != len(set(zone_ids)):
            raise ValueError("irrigationZones must have unique zoneId values")
        if sum(zone.areaHectares for zone in self.irrigationZones) > self.areaHectares:
            raise ValueError("total irrigation zone area cannot exceed the farm area")
        return self


class DeviceSummary(BaseModel):
    deviceId: str
    deviceType: str
    model: str
    protocol: str
    zoneId: str | None
    status: str


class FarmResponse(BaseModel):
    farmId: str
    name: str
    propertyIdentificationCode: str
    farmType: FarmType
    location: Location
    areaHectares: float
    timezone: str
    ownerUserId: str
    status: str
    irrigationZones: list[IrrigationZone]
    devices: list[DeviceSummary]
    version: int
    createdAt: datetime
    updatedAt: datetime
