"""Device Registry component: device ownership and lifecycle (onboarding, decommissioning)."""

from __future__ import annotations

from datetime import datetime, timezone

from shared.errors import not_found
from shared.security import GatewayClaims

from ..events.domain_event_publisher import DomainEventPublisher
from ..repository.farm_device_repository import FarmDeviceRepository
from ..security.access_policy_guard import AccessPolicyGuard


class DeviceRegistry:
    def __init__(self, repository: FarmDeviceRepository, publisher: DomainEventPublisher, guard: AccessPolicyGuard):
        self._repository = repository
        self._publisher = publisher
        self._guard = guard

    def decommission_device(self, farm_id: str, device_id: str, claims: GatewayClaims) -> None:
        farm = self._repository.get_farm(farm_id)
        if farm is None:
            raise not_found("FARM_NOT_FOUND", f"Farm {farm_id} was not found.")
        self._guard.ensure_can_manage_farm(claims, farm)

        device = self._repository.get_device(device_id)
        if device is None or device["farmId"] != farm_id or device["status"] != "ACTIVE":
            raise not_found("DEVICE_NOT_FOUND", f"Device {device_id} is not an active device of farm {farm_id}.")

        # Soft delete: the record is retained for audit, but the device stops being part of the farm.
        device.update(
            status="DECOMMISSIONED",
            decommissionedAt=datetime.now(timezone.utc).isoformat(),
            decommissionedBy=claims.user_id,
        )
        self._repository.save_device(device)
        self._publisher.device_decommissioned(device)
