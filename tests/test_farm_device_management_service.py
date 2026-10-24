"""Endpoints 1, 2, 3 and 8 - Farm and Device Management Service."""

from conftest import AGRONOMIST, MANAGER

NEW_FARM = {
    "name": "Wattle Creek Vineyard",
    "propertyIdentificationCode": "SA123456",
    "farmType": "VITICULTURE",
    "location": {"state": "SA", "region": "Barossa Valley", "latitude": -34.5333, "longitude": 138.95},
    "areaHectares": 64.0,
    "timezone": "Australia/Adelaide",
    "irrigationZones": [{"zoneId": "ZONE-A", "name": "Shiraz Block", "areaHectares": 30.0, "cropType": "Shiraz grapes"}],
}


def _farm_001_body(**changes):
    body = {
        "name": "Riverbend Orchards",
        "propertyIdentificationCode": "3RBOR001",
        "farmType": "HORTICULTURE",
        "location": {"state": "VIC", "region": "Goulburn Valley", "latitude": -36.3833, "longitude": 145.4},
        "areaHectares": 120.5,
        "timezone": "Australia/Melbourne",
        "irrigationZones": [
            {"zoneId": "ZONE-A", "name": "North Block", "areaHectares": 45.0, "cropType": "Apples"},
            {"zoneId": "ZONE-B", "name": "South Block", "areaHectares": 38.0, "cropType": "Pears"},
        ],
    }
    body.update(changes)
    return body


# Endpoint 1
def test_register_farm_returns_201_with_location(farm):
    r = farm.post("/api/v1/farms", json=NEW_FARM, headers=MANAGER)
    assert r.status_code == 201
    assert r.headers["location"] == "/api/v1/farms/FARM-003"
    body = r.json()
    assert body["farmId"] == "FARM-003" and body["ownerUserId"] == "USR-101" and body["version"] == 1
    assert r.headers["x-correlation-id"]


def test_register_duplicate_pic_returns_409(farm):
    farm.post("/api/v1/farms", json=NEW_FARM, headers=MANAGER)
    r = farm.post("/api/v1/farms", json=NEW_FARM, headers=MANAGER)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "DUPLICATE_PROPERTY_IDENTIFICATION_CODE"


def test_register_invalid_location_returns_422(farm):
    bad = {**NEW_FARM, "location": {**NEW_FARM["location"], "latitude": 51.5}}
    r = farm.post("/api/v1/farms", json=bad, headers=MANAGER)
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["field"] == "location.latitude"


def test_register_without_gateway_claims_returns_401(farm):
    assert farm.post("/api/v1/farms", json=NEW_FARM).status_code == 401


def test_agronomist_cannot_register_farm(farm):
    r = farm.post("/api/v1/farms", json=NEW_FARM, headers=AGRONOMIST)
    assert r.status_code == 403 and r.json()["error"]["code"] == "ROLE_NOT_PERMITTED"


# ---- Endpoint 2: GET /api/v1/farms/{farmId} -------------------------------------------
def test_get_farm_returns_zones_and_devices(farm):
    r = farm.get("/api/v1/farms/FARM-001", headers=MANAGER)
    assert r.status_code == 200
    body = r.json()
    assert len(body["irrigationZones"]) == 2 and len(body["devices"]) == 6


def test_get_unknown_farm_returns_404(farm):
    r = farm.get("/api/v1/farms/FARM-999", headers=MANAGER)
    assert r.status_code == 404 and r.json()["error"]["code"] == "FARM_NOT_FOUND"


def test_get_other_tenants_farm_returns_403(farm):
    r = farm.get("/api/v1/farms/FARM-002", headers=MANAGER)
    assert r.status_code == 403 and r.json()["error"]["code"] == "FARM_ACCESS_DENIED"


def test_owner_can_read_newly_registered_farm(farm):
    farm.post("/api/v1/farms", json=NEW_FARM, headers=MANAGER)
    assert farm.get("/api/v1/farms/FARM-003", headers=MANAGER).status_code == 200


# ---- Endpoint 3: PUT /api/v1/farms/{farmId} -------------------------------------------
def test_update_farm_returns_200_and_increments_version(farm):
    r = farm.put("/api/v1/farms/FARM-001", json=_farm_001_body(areaHectares=125.0), headers=MANAGER)
    assert r.status_code == 200
    assert r.json()["areaHectares"] == 125.0 and r.json()["version"] == 2


def test_update_removing_zone_with_devices_returns_409(farm):
    body = _farm_001_body(irrigationZones=[
        {"zoneId": "ZONE-A", "name": "North Block", "areaHectares": 45.0, "cropType": "Apples"}])
    r = farm.put("/api/v1/farms/FARM-001", json=body, headers=MANAGER)
    assert r.status_code == 409 and r.json()["error"]["code"] == "ZONE_HAS_ACTIVE_DEVICES"


def test_update_with_unknown_field_returns_422(farm):
    r = farm.put("/api/v1/farms/FARM-001", json=_farm_001_body(colour="green"), headers=MANAGER)
    assert r.status_code == 422


def test_update_unknown_farm_returns_404(farm):
    assert farm.put("/api/v1/farms/FARM-999", json=_farm_001_body(), headers=MANAGER).status_code == 404


# ---- Endpoint 8: DELETE /api/v1/farms/{farmId}/devices/{deviceId} --------------------
def test_decommission_device_returns_204_then_404(farm):
    r = farm.delete("/api/v1/farms/FARM-001/devices/DEV-1005", headers=MANAGER)
    assert r.status_code == 204 and r.content == b""
    again = farm.delete("/api/v1/farms/FARM-001/devices/DEV-1005", headers=MANAGER)
    assert again.status_code == 404 and again.json()["error"]["code"] == "DEVICE_NOT_FOUND"
    devices = farm.get("/api/v1/farms/FARM-001", headers=MANAGER).json()["devices"]
    assert "DEV-1005" not in [d["deviceId"] for d in devices]


def test_decommission_device_of_another_farm_returns_404(farm):
    r = farm.delete("/api/v1/farms/FARM-001/devices/DEV-2001", headers=MANAGER)
    assert r.status_code == 404


def test_agronomist_cannot_decommission_device(farm):
    assert farm.delete("/api/v1/farms/FARM-001/devices/DEV-1005", headers=AGRONOMIST).status_code == 403
