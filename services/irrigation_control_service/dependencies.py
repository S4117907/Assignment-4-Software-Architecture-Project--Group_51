"""Wires the Irrigation Control Service's components together."""

from __future__ import annotations

from functools import lru_cache

from .audit.audit_logger import AuditLogger
from .dispatch.device_command_dispatcher import DeviceCommandDispatcher
from .domain.command_safety_validator import CommandSafetyValidator
from .domain.irrigation_command_manager import IrrigationCommandManager
from .events.command_status_consumer import CommandStatusConsumer
from .events.zone_actuator_directory import ZoneActuatorDirectory
from .repository.command_repository import CommandRepository
from .security.access_policy_guard import AccessPolicyGuard


@lru_cache(maxsize=1)
def command_manager() -> IrrigationCommandManager:
    repository = CommandRepository()
    return IrrigationCommandManager(
        AccessPolicyGuard(),
        CommandSafetyValidator(ZoneActuatorDirectory(), repository),
        repository,
        DeviceCommandDispatcher(),
        AuditLogger(),
        CommandStatusConsumer(repository),
    )


def reset() -> None:
    command_manager.cache_clear()
