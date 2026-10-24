"""Shared test fixtures: each test gets a fresh event-bus directory and fresh in-memory data."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.farm_device_management_service import dependencies as farm_deps
from services.farm_device_management_service.main import app as farm_app
from services.irrigation_control_service import dependencies as irrigation_deps
from services.irrigation_control_service.main import app as irrigation_app
from services.monitoring_alert_service import dependencies as monitoring_deps
from services.monitoring_alert_service.main import app as monitoring_app
from services.telemetry_ingestion_service import dependencies as telemetry_deps
from services.telemetry_ingestion_service.main import app as telemetry_app

MANAGER = {"X-User-Id": "USR-101", "X-User-Role": "FARM_MANAGER", "X-Farm-Access": "FARM-001"}
AGRONOMIST = {"X-User-Id": "USR-301", "X-User-Role": "AGRONOMIST", "X-Farm-Access": "FARM-001,FARM-002"}
GATEWAY = {"X-User-Id": "GW-FARM-001", "X-User-Role": "DEVICE_GATEWAY", "X-Farm-Access": "FARM-001"}
OPS = {"X-User-Id": "USR-900", "X-User-Role": "OPERATIONS_SUPPORT", "X-Farm-Access": "*"}


@pytest.fixture(autouse=True)
def fresh_state(tmp_path, monkeypatch):
    monkeypatch.setenv("OZAGRIMATE_EVENT_BUS_DIR", str(tmp_path / "bus"))
    for deps in (farm_deps, telemetry_deps, monitoring_deps, irrigation_deps):
        deps.reset()
    yield


@pytest.fixture
def farm():
    return TestClient(farm_app)


@pytest.fixture
def telemetry():
    return TestClient(telemetry_app)


@pytest.fixture
def monitoring():
    return TestClient(monitoring_app)


@pytest.fixture
def irrigation():
    return TestClient(irrigation_app)
