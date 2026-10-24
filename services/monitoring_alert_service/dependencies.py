"""Wires the Monitoring and Alert Service's components together."""

from __future__ import annotations

from functools import lru_cache

from .consumers.farm_directory import FarmDirectory
from .consumers.telemetry_event_consumer import TelemetryEventConsumer
from .domain.alert_manager import AlertManager
from .domain.threshold_rule_engine import ThresholdRuleEngine
from .events.alert_event_publisher import AlertEventPublisher
from .repository.alert_repository import AlertRepository


@lru_cache(maxsize=1)
def alert_manager() -> AlertManager:
    return AlertManager(AlertRepository(), ThresholdRuleEngine(), AlertEventPublisher(), FarmDirectory())


@lru_cache(maxsize=1)
def telemetry_consumer() -> TelemetryEventConsumer:
    return TelemetryEventConsumer(alert_manager())


def reset() -> None:
    alert_manager.cache_clear()
    telemetry_consumer.cache_clear()
