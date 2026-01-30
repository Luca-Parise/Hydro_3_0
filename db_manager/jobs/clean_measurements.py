import pandas as pd
from hampel import hampel

from db_manager.db.conn import get_conn
from db_manager.db.sql_loader import load_sql
from db_manager.config.settings import HAMPEL_WINDOW_SIZE, HAMPEL_SIGMA_THRESHOLD


JOB_NAME = "clean_measurements"
MAX_NUMERIC = 9_999_999.999
MIN_NUMERIC = -9_999_999.999

def _get_last_ts(cur):
    # Read last processed timestamp (ms) from ETL state.
    cur.execute("""
                SELECT last_parent_timestampmsec
                FROM hydro.tab_etl_state
                WHERE job_name = %s;
                """, (JOB_NAME,))
    row = cur.fetchone()
    return row[0] if row else 0

def _clamp_numeric(value):
    if value is None:
        return None
    if value > MAX_NUMERIC:
        return MAX_NUMERIC
    if value < MIN_NUMERIC:
        return MIN_NUMERIC
    return value

def _update_last_ts(cur, ts):
    # Persist last processed timestamp (ms) for incremental runs.
    cur.execute("""
                INSERT INTO hydro.tab_etl_state (job_name, last_parent_timestampmsec, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (job_name)
                DO UPDATE SET last_parent_timestampmsec = EXCLUDED.last_parent_timestampmsec,
                updated_at = EXCLUDED.updated_at
                """, (JOB_NAME, ts))


def clean_measurements():
    # Load SQL upsert for tab_measurements_clean.
    sql_upsert = load_sql("upsert_cleaned_measurements.sql")

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Fetch only new measurements (incremental).
            last_ts = _get_last_ts(cur)

            cur.execute("""
                        SELECT device_id, ts_s, instant_flow_rate_2
            FROM hydro.tab_measurements
            WHERE extract(epoch FROM ts_s) * 1000 > %s
            ORDER BY device_id, ts_s;
            """, (last_ts,))
            rows = cur.fetchall()

        if not rows:
            print("No new measurements to clean.")
            return

        df = pd.DataFrame(rows, columns=["device_id", "ts_s", "flow_raw"])

        out_params = []
        max_ts = last_ts
        for device_id, group in df.groupby("device_id"):
            # Apply Hampel filter per device.
            series = group["flow_raw"].astype(float)

            result = hampel(series, window_size=HAMPEL_WINDOW_SIZE, n_sigma=HAMPEL_SIGMA_THRESHOLD)
            filtered = result.filtered_data
            outlier_indices = set(result.outlier_indices)
            medians = result.medians
            thresholds = result.thresholds

            for i, (idx, row) in enumerate(group.iterrows()):
                ts_s = row["ts_s"]
                ts_msec = int(ts_s.timestamp() * 1000)
                max_ts = max(max_ts, ts_msec)

                is_outlier = i in outlier_indices
                # Prepare row for upsert in tab_measurements_clean.
                out_params.append((
                    device_id,
                    ts_s,
                    _clamp_numeric(float(row["flow_raw"])),
                    _clamp_numeric(float(filtered[i])),
                    bool(is_outlier),
                    _clamp_numeric(float(medians[i])) if medians is not None else None,
                    _clamp_numeric(float(thresholds[i])) if thresholds is not None else None
                ))

        with conn.cursor() as cur:
            cur.executemany(sql_upsert, out_params)
            _update_last_ts(cur, max_ts)
        conn.commit()
        print(f"[clean_measurements] upserted {len(out_params)} rows")
