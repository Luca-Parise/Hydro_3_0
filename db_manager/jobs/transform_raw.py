from db_manager.db.conn import get_conn
from db_manager.db.sql_loader import load_sql

def transform_raw_to_measurements():
    sql = load_sql("transform_raw_to_measurements.sql")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        