INSERT INTO hydro.tab_measurements_clean (
    id_misuratore,
    data_misurazione,
    flow_ls_raw,
    flow_ls_smoothed,
    is_outlier,
    window_median,
    thresholds
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id_misuratore, data_misurazione)
DO UPDATE SET
    flow_ls_raw = EXCLUDED.flow_ls_raw,
    flow_ls_smoothed = EXCLUDED.flow_ls_smoothed,
    is_outlier = EXCLUDED.is_outlier,
    window_median = EXCLUDED.window_median,
    thresholds = EXCLUDED.thresholds,
    updated_at = now();
