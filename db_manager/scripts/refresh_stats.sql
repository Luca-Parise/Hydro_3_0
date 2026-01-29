--2) Popolare/aggiornare tab_statistiche_misuratori (UPSERT)
INSERT INTO hydro.tab_statistiche_misuratori (
  id_misuratore,
  total_measurements,
  first_measurement,
  last_measurement,
  avg_24h,
  avg_7d,
  avg_30d,
  avg_360d,
  avg_all_time,
  updated_at
)
WITH base AS (
  SELECT
    id_misuratore,
    data_misurazione,
    flow_ls_smoothed AS flow
  FROM hydro.tab_measurements_clean
  WHERE flow_ls_smoothed IS NOT NULL
    AND COALESCE(is_outlier, false) = false
),
last_per_sensor AS (
  SELECT
    id_misuratore,
    MAX(data_misurazione) AS last_ts,
    MIN(data_misurazione) AS first_ts,
    COUNT(*)::bigint      AS total_measurements
  FROM base
  GROUP BY id_misuratore
),
agg AS (
  SELECT
    l.id_misuratore,
    l.total_measurements,
    l.first_ts AS first_measurement,
    l.last_ts  AS last_measurement,

    AVG(b.flow) FILTER (WHERE b.data_misurazione >= l.last_ts - interval '24 hours') AS avg_24h,
    AVG(b.flow) FILTER (WHERE b.data_misurazione >= l.last_ts - interval '7 days')   AS avg_7d,
    AVG(b.flow) FILTER (WHERE b.data_misurazione >= l.last_ts - interval '30 days')  AS avg_30d,
    AVG(b.flow) FILTER (WHERE b.data_misurazione >= l.last_ts - interval '360 days') AS avg_360d,
    AVG(b.flow)                                                                      AS avg_all_time,

    now() AS updated_at
  FROM last_per_sensor l
  JOIN base b
    ON b.id_misuratore = l.id_misuratore
  GROUP BY
    l.id_misuratore, l.total_measurements, l.first_ts, l.last_ts
)
SELECT * FROM agg
ON CONFLICT (id_misuratore)
DO UPDATE SET
  total_measurements = EXCLUDED.total_measurements,
  first_measurement  = EXCLUDED.first_measurement,
  last_measurement   = EXCLUDED.last_measurement,
  avg_24h            = EXCLUDED.avg_24h,
  avg_7d             = EXCLUDED.avg_7d,
  avg_30d            = EXCLUDED.avg_30d,
  avg_360d           = EXCLUDED.avg_360d,
  avg_all_time       = EXCLUDED.avg_all_time,
  updated_at         = EXCLUDED.updated_at;