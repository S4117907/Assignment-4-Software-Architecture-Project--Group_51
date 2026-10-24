"""Endpoints 4, 5 and 6 plus the telemetry -> event -> alert flow."""

from datetime import datetime, timedelta, timezone

from conftest import AGRONOMIST, GATEWAY, MANAGER


def _reading(event_id="EVT-1001-000123", minutes_ago=0, readings=None, device="DEV-1001", farm_id="FARM-001"):
    recorded = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()
    return {
        "eventId": event_id,
        "farmId": farm_id,
        "deviceId": device,
        "recordedAt": recorded,
        "readings": readings or [
            {"metric": "SOIL_MOISTURE", "value": 0.142, "unit": "FRACTION"},
            {"metric": "SOIL_TEMPERATURE", "value": 64.4, "unit": "FAHRENHEIT"},
        ],
    }


# Endpoint 4: POST /api/v1/telemetry 
def test_submit_telemetry_normalises_units_and_returns_202(telemetry):
    r = telemetry.post("/api/v1/telemetry", json=_reading(), headers=GATEWAY)
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "ACCEPTED" and body["publishedTo"] == "telemetry.received"
    assert body["readings"] == [
        {"metric": "SOIL_MOISTURE", "value": 14.2, "unit": "PERCENT"},
        {"metric": "SOIL_TEMPERATURE", "value": 18.0, "unit": "CELSIUS"},
    ]


def test_duplicate_event_is_idempotent_200(telemetry):
    telemetry.post("/api/v1/telemetry", json=_reading(), headers=GATEWAY)
    r = telemetry.post("/api/v1/telemetry", json=_reading(), headers=GATEWAY)
    assert r.status_code == 200 and r.json()["status"] == "DUPLICATE_IGNORED"


def test_out_of_range_reading_is_quarantined_422(telemetry):
    bad = _reading(readings=[{"metric": "SOIL_MOISTURE", "value": 140, "unit": "PERCENT"}])
    r = telemetry.post("/api/v1/telemetry", json=bad, headers=GATEWAY)
    assert r.status_code == 422 and r.json()["error"]["code"] == "READING_REJECTED"
    from services.telemetry_ingestion_service.dependencies import repository
    assert repository().quarantined[-1]["reason"] == "READING_REJECTED"


def test_unregistered_device_returns_404(telemetry):
    r = telemetry.post("/api/v1/telemetry", json=_reading(device="DEV-9999"), headers=GATEWAY)
    assert r.status_code == 404 and r.json()["error"]["code"] == "DEVICE_NOT_REGISTERED"


def test_farm_manager_cannot_post_device_telemetry(telemetry):
    assert telemetry.post("/api/v1/telemetry", json=_reading(), headers=MANAGER).status_code == 403


def test_missing_timezone_offset_returns_422(telemetry):
    body = _reading()
    body["recordedAt"] = "2026-10-14T09:15:00"
    assert telemetry.post("/api/v1/telemetry", json=body, headers=GATEWAY).status_code == 422


# Endpoint 5: GET /api/v1/farms/{farmId}/telemetry/latest 
def test_latest_telemetry_flags_stale_readings(telemetry):
    r = telemetry.get("/api/v1/farms/FARM-001/telemetry/latest", headers=AGRONOMIST)
    assert r.status_code == 200
    readings = {(x["deviceId"], x["metric"]): x for x in r.json()["readings"]}
    assert readings[("DEV-1005", "SOIL_MOISTURE")]["stale"] is True
    assert readings[("DEV-1001", "SOIL_MOISTURE")]["stale"] is False


def test_late_buffered_reading_does_not_overwrite_newer_value(telemetry):
    telemetry.post("/api/v1/telemetry", json=_reading(event_id="EVT-NEW-0001"), headers=GATEWAY)
    late = _reading(event_id="EVT-OLD-0001", minutes_ago=30,
                    readings=[{"metric": "SOIL_MOISTURE", "value": 50, "unit": "PERCENT"}])
    r = telemetry.post("/api/v1/telemetry", json=late, headers=GATEWAY)
    assert r.status_code == 202 and r.json()["lateArrival"] is True
    latest = telemetry.get("/api/v1/farms/FARM-001/telemetry/latest?metric=SOIL_MOISTURE&zoneId=ZONE-A",
                           headers=MANAGER).json()["readings"]
    assert latest[0]["value"] == 14.2


def test_latest_unknown_farm_404_and_invalid_metric_422(telemetry):
    assert telemetry.get("/api/v1/farms/FARM-999/telemetry/latest", headers=MANAGER).status_code == 404
    assert telemetry.get("/api/v1/farms/FARM-001/telemetry/latest?metric=COLOUR", headers=MANAGER).status_code == 422


def test_latest_other_tenant_403(telemetry):
    assert telemetry.get("/api/v1/farms/FARM-002/telemetry/latest", headers=MANAGER).status_code == 403


# Endpoint 6: GET /api/v1/farms/{farmId}/alerts
def test_list_seeded_alerts(monitoring):
    r = monitoring.get("/api/v1/farms/FARM-001/alerts", headers=MANAGER)
    assert r.status_code == 200 and r.json()["count"] == 2


def test_low_moisture_telemetry_raises_alert_via_broker(telemetry, monitoring):
    telemetry.post("/api/v1/telemetry", json=_reading(), headers=GATEWAY)  # 14.2 % < 20 % warning
    r = monitoring.get("/api/v1/farms/FARM-001/alerts?status=OPEN", headers=MANAGER)
    alerts = r.json()["alerts"]
    assert r.status_code == 200 and len(alerts) == 1
    assert alerts[0]["alertType"] == "LOW_SOIL_MOISTURE" and alerts[0]["sourceEventId"] == "EVT-1001-000123"


def test_critical_alert_uses_two_channels_and_repeats_do_not_storm(telemetry, monitoring):
    critical = [{"metric": "SOIL_MOISTURE", "value": 8.0, "unit": "PERCENT"}]
    telemetry.post("/api/v1/telemetry", json=_reading(event_id="EVT-C-0001", readings=critical), headers=GATEWAY)
    telemetry.post("/api/v1/telemetry", json=_reading(event_id="EVT-C-0002", readings=critical), headers=GATEWAY)
    alerts = monitoring.get("/api/v1/farms/FARM-001/alerts?severity=CRITICAL&status=OPEN",
                            headers=MANAGER).json()["alerts"]
    assert len(alerts) == 1 and alerts[0]["occurrenceCount"] == 2
    assert {n["channel"] for n in alerts[0]["notifications"]} == {"SMS", "PUSH"}


def test_alerts_errors(monitoring):
    assert monitoring.get("/api/v1/farms/FARM-999/alerts", headers=MANAGER).status_code == 404
    assert monitoring.get("/api/v1/farms/FARM-002/alerts", headers=MANAGER).status_code == 403
    assert monitoring.get("/api/v1/farms/FARM-001/alerts?status=MAYBE", headers=MANAGER).status_code == 422
    assert monitoring.get("/api/v1/farms/FARM-001/alerts").status_code == 401


# Cross-service consistency through events
def test_decommissioned_device_is_rejected_by_telemetry_service(farm, telemetry):
    assert farm.delete("/api/v1/farms/FARM-001/devices/DEV-1001", headers=MANAGER).status_code == 204
    r = telemetry.post("/api/v1/telemetry", json=_reading(), headers=GATEWAY)
    assert r.status_code == 404 and r.json()["error"]["code"] == "DEVICE_NOT_REGISTERED"
