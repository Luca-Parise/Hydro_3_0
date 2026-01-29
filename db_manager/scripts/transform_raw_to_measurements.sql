WITH last_state AS (
    SELECT last_parent_timestampmsec
    FROM hydro.tab_etl_state
    WHERE job_name = 'transform_raw_to_measurements'
),
raw_filtered AS (
    SELECT *
    FROM hydro.tab_measurements_raw
    WHERE parent_timestampmsec > COALESCE((SELECT last_parent_timestampmsec FROM last_state), 0)
),
agg AS (
    SELECT
        device_id,
        parent_timestampmsec,
        to_timestamp(parent_timestampmsec / 1000.0) AS ts_s,
        MAX(raw_data) FILTER (WHERE measure_name = 'Instant flow rate 2') AS instant_flow_rate_2,
        MAX(raw_data) FILTER (WHERE measure_name = 'Instant flow rate 1') AS instant_flow_rate_1,
        MAX(raw_data) FILTER (WHERE measure_name = 'Fluid velocity 2') AS fluid_velocity_2,
        MAX(raw_data) FILTER (WHERE measure_name = 'Fluid velocity 1') AS fluid_velocity_1,
        MAX(raw_data) FILTER (WHERE measure_name = 'Instant heat flow rate 1') AS instant_heat_flow_rate_2,
        MAX(raw_data) FILTER (WHERE measure_name = 'Instant heat flow rate') AS instant_heat_flow_rate_1,
        MAX(raw_data) FILTER (WHERE measure_name = 'Return water temperature 2') AS return_water_temperature_2,
        MAX(raw_data) FILTER (WHERE measure_name = 'Return water temperature 1') AS return_water_temperature_1,
        MAX(raw_data) FILTER (WHERE measure_name = 'Supplying water temperature 1') AS supplying_water_temperature_2,
        MAX(raw_data) FILTER (WHERE measure_name = 'Supplying water temperature') AS supplying_water_temperature_1
    FROM raw_filtered
    GROUP BY device_id, parent_timestampmsec
),
ins AS (
    INSERT INTO hydro.tab_measurements (
    device_id,
    ts_s,
    instant_flow_rate_2,
    instant_flow_rate_1,
    fluid_velocity_2,
    fluid_velocity_1,
    instant_heat_flow_rate_2,
    instant_heat_flow_rate_1,
    return_water_temperature_2,
    return_water_temperature_1,
    supplying_water_temperature_2,
    supplying_water_temperature_1
    )
    SELECT
        device_id,
        ts_s,
        instant_flow_rate_2,
        instant_flow_rate_1,
        fluid_velocity_2,
        fluid_velocity_1,
        instant_heat_flow_rate_2,
        instant_heat_flow_rate_1,
        return_water_temperature_2,
        return_water_temperature_1,
        supplying_water_temperature_2,
        supplying_water_temperature_1
    FROM agg
    ON CONFLICT (device_id, ts_s) DO NOTHING
    RETURNING 1
),
max_raw AS (
    SELECT COALESCE(MAX(parent_timestampmsec), 0) AS max_ts
    FROM raw_filtered
)
INSERT INTO hydro.tab_etl_state (job_name, last_parent_timestampmsec, updated_at)
SELECT 'transform_raw_to_measurements',
    max_ts,
    now()
FROM max_raw
ON CONFLICT (job_name)
DO UPDATE SET
    last_parent_timestampmsec = EXCLUDED.last_parent_timestampmsec,
    updated_at = EXCLUDED.updated_at;
