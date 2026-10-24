"""Device API Router component: exposes device lifecycle endpoints of the open API (v1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Response, status

from shared.security import GatewayClaims, gateway_claims

from ..dependencies import device_registry
from ..domain.device_registry import DeviceRegistry

router = APIRouter(prefix="/api/v1/farms/{farmId}/devices", tags=["Devices"])


@router.delete("/{deviceId}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove a registered device")
def decommission_device(
    farmId: str = Path(pattern=r"^FARM-\d{3,6}$"),
    deviceId: str = Path(pattern=r"^DEV-\d{3,6}$"),
    claims: GatewayClaims = Depends(gateway_claims),
    registry: DeviceRegistry = Depends(device_registry),
) -> Response:
    """Endpoint 8 - DELETE /api/v1/farms/{farmId}/devices/{deviceId}. Returns 204 No Content."""
    registry.decommission_device(farmId, deviceId, claims)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
