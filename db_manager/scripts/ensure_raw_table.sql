CREATE TABLE IF NOT EXISTS {RAW_TABLE_NAME} (
    id BIGSERIAL PRIMARY KEY,
    device_id TEXT,
    group_name TEXT,
    parent_timestamp BIGINT,
    parent_timestampMsec BIGINT,
    measure_name TEXT,
    raw_data DOUBLE PRECISION,
    status INTEGER,
    measure_timestamp BIGINT,
    measure_timestampMsec BIGINT
);

CREATE INDEX IF NOT EXISTS idx_raw_device_ts
ON {RAW_TABLE_NAME} (device_id, measure_timestampMsec);