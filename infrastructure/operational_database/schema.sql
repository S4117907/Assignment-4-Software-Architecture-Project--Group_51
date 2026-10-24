-- Operational Database container: PostgreSQL (Amazon RDS Multi-AZ, ADR 3 / ADR 7).

CREATE SCHEMA farm_device;   -- by Farm and Device Management Service
CREATE SCHEMA monitoring;    -- Monitoring and Alert Service
CREATE SCHEMA irrigation;    -- Irrigation Control Service
CREATE SCHEMA advisory;      -- AI Advisory Service

CREATE TABLE farm_device.farm (
    farm_id                      VARCHAR(12) PRIMARY KEY,
    name                         VARCHAR(100) NOT NULL,
    property_identification_code CHAR(8)      NOT NULL UNIQUE,
    farm_type                    VARCHAR(30)  NOT NULL,
    state                        VARCHAR(3)   NOT NULL,
    region                       VARCHAR(80)  NOT NULL,
    latitude                     NUMERIC(8,5) NOT NULL CHECK (latitude BETWEEN -44 AND -10),
    longitude                    NUMERIC(8,5) NOT NULL CHECK (longitude BETWEEN 112 AND 154),
    area_hectares                NUMERIC(12,2) NOT NULL CHECK (area_hectares > 0),
    timezone                     VARCHAR(40)  NOT NULL,
    owner_user_id                VARCHAR(40)  NOT NULL,
    status                       VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE',
    version                      INTEGER      NOT NULL DEFAULT 1,
    created_at                   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at                   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE farm_device.irrigation_zone (
    farm_id        VARCHAR(12) REFERENCES farm_device.farm(farm_id),
    zone_id        VARCHAR(11),
    name           VARCHAR(60) NOT NULL,
    area_hectares  NUMERIC(10,2) NOT NULL,
    crop_type      VARCHAR(60) NOT NULL,
    PRIMARY KEY (farm_id, zone_id)
);

CREATE TABLE farm_device.device (
    device_id     VARCHAR(12) PRIMARY KEY,
    farm_id       VARCHAR(12) NOT NULL REFERENCES farm_device.farm(farm_id),
    zone_id       VARCHAR(11),
    device_type   VARCHAR(40) NOT NULL,
    model         VARCHAR(60) NOT NULL,
    protocol      VARCHAR(10) NOT NULL CHECK (protocol IN ('MQTT', 'HTTPS')),
    status        VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    decommissioned_at TIMESTAMPTZ,
    decommissioned_by VARCHAR(40)
);

CREATE TABLE monitoring.alert (
    alert_id         VARCHAR(12) PRIMARY KEY,
    farm_id          VARCHAR(12) NOT NULL,
    alert_type       VARCHAR(40) NOT NULL,
    severity         VARCHAR(10) NOT NULL,
    status           VARCHAR(15) NOT NULL,
    device_id        VARCHAR(12) NOT NULL,
    metric           VARCHAR(30) NOT NULL,
    observed_value   NUMERIC(10,2) NOT NULL,
    threshold        NUMERIC(10,2) NOT NULL,
    triggered_at     TIMESTAMPTZ NOT NULL,
    last_observed_at TIMESTAMPTZ NOT NULL,
    occurrence_count INTEGER NOT NULL DEFAULT 1,
    source_event_id  VARCHAR(64) NOT NULL
);

CREATE TABLE irrigation.command (
    command_id       VARCHAR(12) PRIMARY KEY,
    farm_id          VARCHAR(12) NOT NULL,
    zone_id          VARCHAR(11) NOT NULL,
    action           VARCHAR(5)  NOT NULL CHECK (action IN ('START', 'STOP')),
    duration_minutes INTEGER CHECK (duration_minutes BETWEEN 1 AND 720),
    source           VARCHAR(20) NOT NULL,
    recommendation_id VARCHAR(44),
    requested_by     VARCHAR(40) NOT NULL,
    status           VARCHAR(25) NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL
);

CREATE TABLE irrigation.audit_record (            -- hash-chained, append-only (ASR22)
    audit_record_id VARCHAR(12) PRIMARY KEY,
    actor           VARCHAR(40) NOT NULL,
    action          VARCHAR(40) NOT NULL,
    details         JSONB       NOT NULL,
    recorded_at     TIMESTAMPTZ NOT NULL,
    previous_hash   CHAR(64)    NOT NULL,
    hash            CHAR(64)    NOT NULL UNIQUE
);
REVOKE UPDATE, DELETE ON irrigation.audit_record FROM PUBLIC;
