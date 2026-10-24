"""Request and response contracts for the Irrigation Control Service (API v1)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IrrigationAction(str, Enum):
    START = "START"
    STOP = "STOP"


class CommandSource(str, Enum):
    MANUAL = "MANUAL"
    AI_RECOMMENDATION = "AI_RECOMMENDATION"


class IrrigationCommandRequest(BaseModel):
    """Body for POST /api/v1/farms/{farmId}/irrigation-commands."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "zoneId": "ZONE-A",
                "action": "START",
                "durationMinutes": 45,
                "flowRateLitresPerMinute": 120,
                "source": "MANUAL",
            }
        },
    )

    zoneId: str = Field(pattern=r"^ZONE-[A-Z0-9]{1,6}$")
    action: IrrigationAction
    durationMinutes: int | None = Field(default=None, ge=1, le=720)
    flowRateLitresPerMinute: float | None = Field(default=None, gt=0, le=2000)
    source: CommandSource = CommandSource.MANUAL
    recommendationId: str | None = Field(default=None, pattern=r"^REC-[A-Za-z0-9\-]{3,40}$")
    confirmedByUserId: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def _action_rules(self) -> "IrrigationCommandRequest":
        if self.action is IrrigationAction.START and self.durationMinutes is None:
            raise ValueError("durationMinutes is required when action is START")
        if self.action is IrrigationAction.STOP and (self.durationMinutes or self.flowRateLitresPerMinute):
            raise ValueError("durationMinutes and flowRateLitresPerMinute must be omitted when action is STOP")
        if self.source is CommandSource.AI_RECOMMENDATION and not self.recommendationId:
            raise ValueError("recommendationId is required when source is AI_RECOMMENDATION")
        return self


class DispatchDetails(BaseModel):
    targetDeviceId: str
    protocol: str
    topic: str
    qos: int
    acknowledgementDeadline: datetime


class IrrigationCommandAccepted(BaseModel):
    commandId: str
    farmId: str
    zoneId: str
    action: IrrigationAction
    durationMinutes: int | None
    flowRateLitresPerMinute: float | None
    source: CommandSource
    recommendationId: str | None
    requestedBy: str
    status: str
    createdAt: datetime
    dispatch: DispatchDetails
    auditRecordId: str
