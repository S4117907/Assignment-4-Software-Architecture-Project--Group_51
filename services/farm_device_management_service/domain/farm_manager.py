"""Farm Manager component: business rules for registering and updating farms."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shared.errors import conflict, not_found
from shared.security import GatewayClaims

from ..events.domain_event_publisher import DomainEventPublisher
from ..repository.farm_device_repository import FarmDeviceRepository
from ..schemas.farm_schemas import FarmRequest
from ..security.access_policy_guard import AccessPolicyGuard


class FarmManager:
    def __init__(self, repository: FarmDeviceRepository, publisher: DomainEventPublisher, guard: AccessPolicyGuard):
        self._repository = repository
        self._publisher = publisher
        self._guard = guard

    def register_farm(self, request: FarmRequest, claims: GatewayClaims) -> dict[str, Any]:
        self._guard.ensure_can_register_farm(claims)
        existing = self._repository.find_farm_by_pic(request.propertyIdentificationCode)
        if existing:
            raise conflict(
                "DUPLICATE_PROPERTY_IDENTIFICATION_CODE",
                f"PIC {request.propertyIdentificationCode} is already registered to {existing['farmId']}.",
            )
        now = datetime.now(timezone.utc)
        farm = {
            "farmId": self._repository.next_farm_id(),
            **request.model_dump(mode="json"),
            "ownerUserId": claims.user_id,
            "status": "ACTIVE",
            "version": 1,
            "createdAt": now,
            "updatedAt": now,
        }
        self._repository.save_farm(farm)
        self._publisher.farm_registered(farm)
        return self._with_devices(farm)

    def get_farm(self, farm_id: str, claims: GatewayClaims) -> dict[str, Any]:
        farm = self._require_farm(farm_id)
        self._guard.ensure_can_view_farm(claims, farm)
        return self._with_devices(farm)

    def update_farm(self, farm_id: str, request: FarmRequest, claims: GatewayClaims) -> dict[str, Any]:
        farm = self._require_farm(farm_id)
        self._guard.ensure_can_manage_farm(claims, farm)

        other = self._repository.find_farm_by_pic(request.propertyIdentificationCode)
        if other and other["farmId"] != farm_id:
            raise conflict(
                "DUPLICATE_PROPERTY_IDENTIFICATION_CODE",
                f"PIC {request.propertyIdentificationCode} is already registered to {other['farmId']}.",
            )

        # A zone cannot be removed while active devices are still installed in it.
        new_zone_ids = {zone.zoneId for zone in request.irrigationZones}
        stranded = sorted(
            {d["zoneId"] for d in self._repository.devices_for_farm(farm_id) if d["zoneId"]} - new_zone_ids
        )
        if stranded:
            raise conflict(
                "ZONE_HAS_ACTIVE_DEVICES",
                f"Zones {', '.join(stranded)} still have active devices; decommission them before removing the zones.",
            )

        updated = {
            **farm,
            **request.model_dump(mode="json"),
            "version": farm["version"] + 1,
            "updatedAt": datetime.now(timezone.utc),
        }
        self._repository.save_farm(updated)
        self._publisher.farm_updated(updated)
        return self._with_devices(updated)

    def _require_farm(self, farm_id: str) -> dict[str, Any]:
        farm = self._repository.get_farm(farm_id)
        if farm is None:
            raise not_found("FARM_NOT_FOUND", f"Farm {farm_id} was not found.")
        return farm

    def _with_devices(self, farm: dict[str, Any]) -> dict[str, Any]:
        return {**farm, "devices": self._repository.devices_for_farm(farm["farmId"])}
