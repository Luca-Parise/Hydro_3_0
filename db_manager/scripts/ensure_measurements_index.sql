CREATE UNIQUE INDEX IF NOT EXISTS idx_measurements_device_ts
ON hydro.tab_measurements (device_id, ts_s);
