"""Irrigation Command Manager component: creates commands and manages their lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shared.observability import log_event
from shared.security import GatewayClaims

from ..audit.audit_logger import AuditLogger
from ..dispatch.device_command_dispatcher import SERVICE_NAME, DeviceCommandDispatcher
from ..events.command_status_consumer import CommandStatusConsumer
from ..repository.command_repository import CommandRepository
from ..schemas.irrigation_schemas import IrrigationAction, IrrigationCommandRequest
from ..security.access_policy_guard import AccessPolicyGuard
from .command_safety_validator import CommandSafetyValidator


class IrrigationCommandManager:
    def __init__(self, guard: AccessPolicyGuard, validator: CommandSafetyValidator, repository: CommandRepository,
                 dispatcher: DeviceCommandDispatcher, audit: AuditLogger, status_consumer: CommandStatusConsumer):
        self._guard = guard
        self._validator = validator
        self._repository = repository
        self._dispatcher = dispatcher
        self._audit = audit
        self._status_consumer = status_consumer

    def issue(self, farm_id: str, request: IrrigationCommandRequest, claims: GatewayClaims) -> dict[str, Any]:
        self._status_consumer.drain()                 # apply any device acknowledgements first
        self._validator.require_farm(farm_id)          # 404 unknown farm
        self._guard.ensure_can_command(claims, farm_id)  # 403 tenant / role
        self._guard.ensure_human_confirmation(claims, request)  # 403 unconfirmed AI command
        actuator = self._validator.validate(farm_id, request)   # 404 zone, 409 conflicts

        now = datetime.now(timezone.utc)
        command = {
            "commandId": self._repository.next_command_id(),
            "farmId": farm_id,
            "zoneId": request.zoneId,
            "action": request.action.value,
            "durationMinutes": request.durationMinutes,
            "flowRateLitresPerMinute": request.flowRateLitresPerMinute,
            "source": request.source.value,
            "recommendationId": request.recommendationId,
            "requestedBy": claims.user_id,
            "status": "PENDING_DISPATCH",
            "createdAt": now,
        }
        if request.action is IrrigationAction.STOP:
            self._repository.stop_active_for_zone(farm_id, request.zoneId)
        self._repository.save(command)
        command["auditRecordId"] = self._audit.record(
            claims.user_id, f"IRRIGATION_{request.action.value}",
            {"commandId": command["commandId"], "farmId": farm_id, "zoneId": request.zoneId,
             "source": request.source.value, "recommendationId": request.recommendationId},
        )
        command["dispatch"] = self._dispatcher.dispatch(command, actuator, now)
        command["status"] = "DISPATCHED"
        log_event(SERVICE_NAME, "irrigation.command.dispatched", commandId=command["commandId"],
                  farmId=farm_id, zoneId=request.zoneId, action=request.action.value)
        return command
