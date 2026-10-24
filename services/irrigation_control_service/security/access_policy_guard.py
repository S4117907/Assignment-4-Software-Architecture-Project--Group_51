"""Access Policy Guard component (ADR 5).
"""

from __future__ import annotations

from shared.errors import forbidden
from shared.security import GatewayClaims, Role

from ..schemas.irrigation_schemas import CommandSource, IrrigationCommandRequest


class AccessPolicyGuard:
    def ensure_can_command(self, claims: GatewayClaims, farm_id: str) -> None:
        claims.require_farm_access(farm_id)
        claims.require_role(Role.FARM_MANAGER)

    def ensure_human_confirmation(self, claims: GatewayClaims, request: IrrigationCommandRequest) -> None:
        if request.source is CommandSource.AI_RECOMMENDATION and request.confirmedByUserId != claims.user_id:
            raise forbidden(
                "HUMAN_CONFIRMATION_REQUIRED",
                "AI-recommended irrigation must be explicitly confirmed by the requesting farm manager "
                "(confirmedByUserId must match the authenticated user).",
            )
