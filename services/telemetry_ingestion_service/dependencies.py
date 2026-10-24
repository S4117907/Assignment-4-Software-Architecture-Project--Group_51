"""Wires the Telemetry Ingestion Service's components together."""

from __future__ import annotations

from functools import lru_cache

from .adapters.payload_normaliser import PayloadNormaliser
from .domain.deduplication_filter import DeduplicationFilter
from .domain.ingestion_pipeline import IngestionPipeline
from .domain.latest_telemetry_query import LatestTelemetryQuery
from .domain.telemetry_validator import TelemetryValidator
from .events.device_directory_cache import DeviceDirectoryCache
from .events.telemetry_event_publisher import TelemetryEventPublisher
from .repository.telemetry_repository import TelemetryRepository


@lru_cache(maxsize=1)
def repository() -> TelemetryRepository:
    return TelemetryRepository()


@lru_cache(maxsize=1)
def directory() -> DeviceDirectoryCache:
    return DeviceDirectoryCache()


@lru_cache(maxsize=1)
def dedup() -> DeduplicationFilter:
    return DeduplicationFilter()


@lru_cache(maxsize=1)
def publisher() -> TelemetryEventPublisher:
    return TelemetryEventPublisher()


def ingestion_pipeline() -> IngestionPipeline:
    return IngestionPipeline(PayloadNormaliser(), TelemetryValidator(directory()), dedup(), repository(), publisher())


def latest_query() -> LatestTelemetryQuery:
    return LatestTelemetryQuery(repository(), directory())


def reset() -> None:
    for factory in (repository, directory, dedup, publisher):
        factory.cache_clear()
