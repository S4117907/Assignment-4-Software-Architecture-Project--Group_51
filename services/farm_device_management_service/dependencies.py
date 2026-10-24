"""Wires the service's components together (one instance per running service)."""

from __future__ import annotations

from functools import lru_cache

from .domain.device_registry import DeviceRegistry
from .domain.farm_manager import FarmManager
from .events.domain_event_publisher import DomainEventPublisher
from .repository.farm_device_repository import FarmDeviceRepository
from .security.access_policy_guard import AccessPolicyGuard


@lru_cache(maxsize=1)
def repository() -> FarmDeviceRepository:
    return FarmDeviceRepository()


@lru_cache(maxsize=1)
def publisher() -> DomainEventPublisher:
    return DomainEventPublisher()


@lru_cache(maxsize=1)
def guard() -> AccessPolicyGuard:
    return AccessPolicyGuard()


def farm_manager() -> FarmManager:
    return FarmManager(repository(), publisher(), guard())


def device_registry() -> DeviceRegistry:
    return DeviceRegistry(repository(), publisher(), guard())


def reset() -> None:
    """Used by tests to start from clean seed data."""
    repository.cache_clear()
