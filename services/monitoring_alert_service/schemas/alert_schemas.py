"""Response contracts for the Monitoring and Alert Service (API v1)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class Severity(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class NotificationDelivery(BaseModel):
    channel: str
    deliveryStatus: str


class Alert(BaseModel):
    alertId: str
    alertType: str
    severity: Severity
    status: AlertStatus
    message: str
    deviceId: str
    zoneId: str | None
    metric: str
    observedValue: float
    unit: str
    threshold: float
    triggeredAt: datetime
    lastObservedAt: datetime
    occurrenceCount: int
    sourceEventId: str
    notifications: list[NotificationDelivery]


class AlertFilters(BaseModel):
    status: AlertStatus | None
    severity: Severity | None
    limit: int


class AlertListResponse(BaseModel):
    farmId: str
    count: int
    filters: AlertFilters
    alerts: list[Alert]
