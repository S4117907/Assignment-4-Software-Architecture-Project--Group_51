"""Identity claims forwarded by the API Gateway (ADR 5).

The API Gateway validates the JWT issued by the Identity Provider (users sign in with
MFA) and forwards the verified claims to the services as headers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from fastapi import Header

from .errors import forbidden, unauthorized


class Role(str, Enum):
    FARM_MANAGER = "FARM_MANAGER"
    AGRONOMIST = "AGRONOMIST"
    OPERATIONS_SUPPORT = "OPERATIONS_SUPPORT"
    DEVICE_GATEWAY = "DEVICE_GATEWAY"


@dataclass(frozen=True)
class GatewayClaims:
    user_id: str
    role: Role
    farm_access: frozenset[str]

    def can_access_farm(self, farm_id: str) -> bool:
        return "*" in self.farm_access or farm_id in self.farm_access

    def require_role(self, *allowed: Role) -> None:
        if self.role not in allowed:
            allowed_names = ", ".join(r.value for r in allowed)
            raise forbidden(
                "ROLE_NOT_PERMITTED",
                f"Role {self.role.value} cannot perform this action. Allowed roles: {allowed_names}.",
            )

    def require_farm_access(self, farm_id: str) -> None:
        if not self.can_access_farm(farm_id):
            raise forbidden("FARM_ACCESS_DENIED", f"User {self.user_id} has no access to farm {farm_id}.")


def gateway_claims(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    x_farm_access: str | None = Header(default=None, alias="X-Farm-Access"),
) -> GatewayClaims:
    """FastAPI dependency that turns gateway headers into verified claims."""
    if not x_user_id or not x_user_role:
        raise unauthorized(
            "AUTHENTICATION_REQUIRED",
            "Missing identity claims. Requests must pass through the API Gateway with a valid token.",
        )
    try:
        role = Role(x_user_role.strip().upper())
    except ValueError as exc:
        raise unauthorized("UNKNOWN_ROLE", f"Role '{x_user_role}' is not recognised.") from exc
    farms = frozenset(f.strip() for f in (x_farm_access or "").split(",") if f.strip())
    return GatewayClaims(user_id=x_user_id.strip(), role=role, farm_access=farms)
