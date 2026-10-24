"""Endpoint 7 - Irrigation Control Service, plus audit chain and dispatch evidence."""

import json

from conftest import AGRONOMIST, MANAGER

START = {"zoneId": "ZONE-A", "action": "START", "durationMinutes": 45, "flowRateLitresPerMinute": 120, "source": "MANUAL"}
URL = "/api/v1/farms/FARM-001/irrigation-commands"


def test_start_irrigation_returns_202_and_dispatches(irrigation):
    r = irrigation.post(URL, json=START, headers=MANAGER)
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "DISPATCHED" and body["dispatch"]["targetDeviceId"] == "DEV-1003"
    assert body["dispatch"]["topic"] == "ozagrimate/farms/FARM-001/zones/ZONE-A/commands"
    assert body["auditRecordId"] == "AUD-000001"


def test_overlapping_start_returns_409_and_stop_is_allowed(irrigation):
    irrigation.post(URL, json=START, headers=MANAGER)
    r = irrigation.post(URL, json=START, headers=MANAGER)
    assert r.status_code == 409 and r.json()["error"]["code"] == "ZONE_ALREADY_IRRIGATING"
    stop = irrigation.post(URL, json={"zoneId": "ZONE-A", "action": "STOP"}, headers=MANAGER)
    assert stop.status_code == 202
    assert irrigation.post(URL, json=START, headers=MANAGER).status_code == 202


def test_agronomist_cannot_actuate_irrigation(irrigation):
    r = irrigation.post(URL, json=START, headers=AGRONOMIST)
    assert r.status_code == 403 and r.json()["error"]["code"] == "ROLE_NOT_PERMITTED"


def test_unconfirmed_ai_command_returns_403(irrigation):
    ai = {**START, "source": "AI_RECOMMENDATION", "recommendationId": "REC-20261014-07"}
    r = irrigation.post(URL, json=ai, headers=MANAGER)
    assert r.status_code == 403 and r.json()["error"]["code"] == "HUMAN_CONFIRMATION_REQUIRED"
    confirmed = irrigation.post(URL, json={**ai, "confirmedByUserId": "USR-101"}, headers=MANAGER)
    assert confirmed.status_code == 202


def test_invalid_commands_return_422(irrigation):
    assert irrigation.post(URL, json={**START, "durationMinutes": 0}, headers=MANAGER).status_code == 422
    assert irrigation.post(URL, json={"zoneId": "ZONE-A", "action": "START"}, headers=MANAGER).status_code == 422
    assert irrigation.post(URL, json={**START, "action": "OPEN"}, headers=MANAGER).status_code == 422


def test_unknown_farm_and_zone_return_404(irrigation):
    assert irrigation.post("/api/v1/farms/FARM-999/irrigation-commands", json=START, headers=MANAGER).status_code == 404
    r = irrigation.post(URL, json={**START, "zoneId": "ZONE-Z"}, headers=MANAGER)
    assert r.status_code == 404 and r.json()["error"]["code"] == "ZONE_NOT_FOUND"


def test_decommissioned_valve_cannot_be_commanded(farm, irrigation):
    assert farm.delete("/api/v1/farms/FARM-001/devices/DEV-1003", headers=MANAGER).status_code == 204
    r = irrigation.post(URL, json=START, headers=MANAGER)
    assert r.status_code == 409 and r.json()["error"]["code"] == "NO_ACTIVE_ACTUATOR"


def test_audit_chain_is_tamper_evident(irrigation):
    from services.irrigation_control_service.dependencies import command_manager
    irrigation.post(URL, json=START, headers=MANAGER)
    irrigation.post(URL, json={"zoneId": "ZONE-A", "action": "STOP"}, headers=MANAGER)
    audit = command_manager()._audit
    assert audit.verify_chain()
    audit._records[0]["actor"] = "intruder"
    assert not audit.verify_chain()


def test_command_reaches_iot_device_hub_log(irrigation, tmp_path):
    irrigation.post(URL, json=START, headers=MANAGER)
    line = (tmp_path / "bus" / "iot-device-hub.commands.log").read_text().splitlines()[0]
    assert json.loads(line)["payload"]["mqttTopic"].endswith("ZONE-A/commands")
