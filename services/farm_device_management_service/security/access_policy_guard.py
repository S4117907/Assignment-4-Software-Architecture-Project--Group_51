"""Access Policy Guard component (ADR 5).
"""

from __future__ import annotations

from typing import Any

from shared.errors import forbidden
from shared.security import GatewayClaims, Role

MANAGE_ROLES = (Role.FARM_MANAGER, Role.OPERATIONS_SUPPORT)


class AccessPolicyGuard:
    def ensure_can_register_farm(self, claims: GatewayClaims) -> None:
        claims.require_role(*MANAGE_ROLES)

    def ensure_can_view_farm(self, claims: GatewayClaims, farm: dict[str, Any]) -> None:
        if not self._has_tenant_access(claims, farm):
            raise forbidden("FARM_ACCESS_DENIED", f"User {claims.user_id} has no access to farm {farm['farmId']}.")

    def ensure_can_manage_farm(self, claims: GatewayClaims, farm: dict[str, Any]) -> None:
        claims.require_role(*MANAGE_ROLES)
        self.ensure_can_view_farm(claims, farm)

    @staticmethod
    def _has_tenant_access(claims: GatewayClaims, farm: dict[str, Any]) -> bool:
        return claims.can_access_farm(farm["farmId"]) or farm["ownerUserId"] == claims.user_id
