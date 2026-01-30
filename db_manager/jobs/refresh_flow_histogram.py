from db_manager.config.settings import FLOW_HIST_BINS, FLOW_HIST_WINDOW_HOURS
from db_manager.db.conn import get_conn
from db_manager.db.sql_loader import load_sql


def refresh_flow_histogram():
    sql_refresh = load_sql("refresh_flow_histogram.sql")
    sql_refresh = sql_refresh.replace("{BINS}", str(FLOW_HIST_BINS))

    if FLOW_HIST_WINDOW_HOURS <= 0:
        window_start = "TIMESTAMPTZ '1970-01-01 00:00:00+00'"
        window_end = "TIMESTAMPTZ 'infinity'"
        window_filter = "TRUE"
    else:
        window_end = "date_trunc('hour', now())"
        window_start = f"date_trunc('hour', now()) - interval '{FLOW_HIST_WINDOW_HOURS} hours'"
        window_filter = (
            "data_misurazione >= (SELECT window_start FROM params) "
            "AND data_misurazione < (SELECT window_end FROM params)"
        )

    sql_refresh = sql_refresh.replace("{WINDOW_START}", window_start)
    sql_refresh = sql_refresh.replace("{WINDOW_END}", window_end)
    sql_refresh = sql_refresh.replace("{WINDOW_FILTER}", window_filter)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_refresh)
        conn.commit()
    print("Flow histogram refreshed successfully.")
