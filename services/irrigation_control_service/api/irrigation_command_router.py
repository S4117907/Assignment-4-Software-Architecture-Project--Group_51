"""Irrigation Command API Router component (API v1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, status

from shared.security import GatewayClaims, gateway_claims

from ..dependencies import command_manager
from ..domain.irrigation_command_manager import IrrigationCommandManager
from ..schemas.irrigation_schemas import IrrigationCommandAccepted, IrrigationCommandRequest

router = APIRouter(prefix="/api/v1/farms/{farmId}/irrigation-commands", tags=["Irrigation"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=IrrigationCommandAccepted,
             summary="Issue an irrigation command")
def issue_irrigation_command(
    body: IrrigationCommandRequest,
    farmId: str = Path(pattern=r"^FARM-\d{3,6}$"),
    claims: GatewayClaims = Depends(gateway_claims),
    manager: IrrigationCommandManager = Depends(command_manager),
) -> dict:
    """Endpoint 7 - POST /api/v1/farms/{farmId}/irrigation-commands.

    """
    return manager.issue(farmId, body, claims)
