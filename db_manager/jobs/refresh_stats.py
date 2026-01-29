from db_manager.db.conn import get_conn
from db_manager.db.sql_loader import load_sql

def refresh_stats():
    with get_conn() as conn:
        sql = load_sql("refresh_stats.sql")
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
            