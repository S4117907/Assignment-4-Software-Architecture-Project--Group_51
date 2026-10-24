"""Farm API Router component: exposes the farm endpoints of the open API (v1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Response, status

from shared.security import GatewayClaims, gateway_claims

from ..dependencies import farm_manager
from ..domain.farm_manager import FarmManager
from ..schemas.farm_schemas import FarmRequest, FarmResponse

router = APIRouter(prefix="/api/v1/farms", tags=["Farms"])

FARM_ID = Path(pattern=r"^FARM-\d{3,6}$", description="Farm identifier, e.g. FARM-001")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=FarmResponse, summary="Register a farm")
def register_farm(
    body: FarmRequest,
    response: Response,
    claims: GatewayClaims = Depends(gateway_claims),
    manager: FarmManager = Depends(farm_manager),
) -> dict:
    """Endpoint 1 - POST /api/v1/farms. Returns 201 Created and a Location header."""
    farm = manager.register_farm(body, claims)
    response.headers["Location"] = f"/api/v1/farms/{farm['farmId']}"
    return farm


@router.get("/{farmId}", response_model=FarmResponse, summary="Retrieve a farm")
def get_farm(
    farmId: str = FARM_ID,
    claims: GatewayClaims = Depends(gateway_claims),
    manager: FarmManager = Depends(farm_manager),
) -> dict:
    """Endpoint 2 - GET /api/v1/farms/{farmId}. Returns the farm, its zones and active devices."""
    return manager.get_farm(farmId, claims)


@router.put("/{farmId}", response_model=FarmResponse, summary="Update a farm")
def update_farm(
    body: FarmRequest,
    farmId: str = FARM_ID,
    claims: GatewayClaims = Depends(gateway_claims),
    manager: FarmManager = Depends(farm_manager),
) -> dict:
    """Endpoint 3 - PUT /api/v1/farms/{farmId}. Full replacement of the farm's editable details."""
    return manager.update_farm(farmId, body, claims)
