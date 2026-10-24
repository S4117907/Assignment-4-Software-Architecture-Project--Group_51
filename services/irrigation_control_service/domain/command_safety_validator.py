"""
Checks that a command is physically safe and meaningful before anything is sent to
farm equipment: the zone exists, it has an active valve controller, and a START does
not overlap an irrigation run that is already in progress for the same zone.
"""

from __future__ import annotations

from typing import Any

from shared.errors import conflict, not_found

from ..events.zone_actuator_directory import ZoneActuatorDirectory
from ..repository.command_repository import CommandRepository
from ..schemas.irrigation_schemas import IrrigationAction, IrrigationCommandRequest


class CommandSafetyValidator:
    def __init__(self, directory: ZoneActuatorDirectory, repository: CommandRepository):
        self._directory = directory
        self._repository = repository

    def require_farm(self, farm_id: str) -> None:
        if not self._directory.farm_exists(farm_id):
            raise not_found("FARM_NOT_FOUND", f"Farm {farm_id} was not found.")

    def validate(self, farm_id: str, request: IrrigationCommandRequest) -> dict[str, Any]:
        if not self._directory.zone_exists(farm_id, request.zoneId):
            raise not_found("ZONE_NOT_FOUND", f"Irrigation zone {request.zoneId} does not exist on farm {farm_id}.")
        actuator = self._directory.actuator_for(farm_id, request.zoneId)
        if actuator is None:
            raise conflict("NO_ACTIVE_ACTUATOR", f"Zone {request.zoneId} has no active irrigation valve controller.")
        if request.action is IrrigationAction.START:
            running = self._repository.active_start_for_zone(farm_id, request.zoneId)
            if running:
                raise conflict(
                    "ZONE_ALREADY_IRRIGATING",
                    f"Zone {request.zoneId} already has active command {running['commandId']}; "
                    "send a STOP command or wait for it to finish.",
                )
        return actuator
