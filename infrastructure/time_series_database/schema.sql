-- Time-Series Database container: TimescaleDB (PostgreSQL extension), ADR 7.

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE telemetry_reading (
    recorded_at     TIMESTAMPTZ NOT NULL,      -- original device timestamp (ASR9)
    received_at     TIMESTAMPTZ NOT NULL,      -- platform receipt timestamp (ASR13)
    farm_id         VARCHAR(12) NOT NULL,
    device_id       VARCHAR(12) NOT NULL,
    zone_id         VARCHAR(11),
    metric          VARCHAR(30) NOT NULL,
    value           DOUBLE PRECISION NOT NULL,
    unit            VARCHAR(25) NOT NULL,
    source_event_id VARCHAR(64) NOT NULL,
    UNIQUE (source_event_id, metric, recorded_at)   -- idempotent re-delivery (ASR10)
);

-- Partition by time (1-day chunks) and by farm (space partitioning) for scalability (ADR 2).
SELECT create_hypertable('telemetry_reading', 'recorded_at',
                         partitioning_column => 'farm_id', number_partitions => 16,
                         chunk_time_interval => INTERVAL '1 day');


ALTER TABLE telemetry_reading SET (timescaledb.compress, timescaledb.compress_segmentby = 'farm_id, device_id');
SELECT add_compression_policy('telemetry_reading', INTERVAL '7 days');
SELECT add_retention_policy('telemetry_reading', INTERVAL '730 days');

CREATE TABLE quarantined_telemetry (               -- rejected readings kept for investigation (ASR12)
    received_at TIMESTAMPTZ NOT NULL,
    reason      VARCHAR(40) NOT NULL,
    payload     JSONB       NOT NULL
);
