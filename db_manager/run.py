from db_manager.db.conn import get_conn
from db_manager.db.schema import ensure_raw_table, ensure_etl_state_table, ensure_measurements_index
from db_manager.jobs.ingest_eventhub import load_eventhub_configs, start_consumers
from db_manager.jobs.transform_raw import transform_raw_to_measurements

from db_manager.config.settings import RAW_TABLE_NAME, SECONDS_BETWEEN_RAW_TO_MEASUREMENTS_TRANSFORM

from time import sleep
import threading 


def start_transform_scheduler(interval_seconds=300):
    def loop():
        i = 1
        while True: 
            try:
                transform_raw_to_measurements()
                print(f"Transform job {i} executed successfully.")
                i += 1
            except Exception as e:
                print(f"Error executing transform job {i}: {e}")
            sleep(interval_seconds)
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()


def main():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        print("Connection to database successful")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

    eventhub_configs = load_eventhub_configs()

    try:
        ensure_raw_table()
        ensure_etl_state_table()
        ensure_measurements_index()
        print(f"\nTable {RAW_TABLE_NAME} checked/created successfully.\n")
    except Exception as e:
        print(f"Error creating/checking table {RAW_TABLE_NAME}: {e}")
        raise

    if not eventhub_configs:
        print("No valid eventhub configurations found.")
        raise RuntimeError("No valid eventhub configurations found.")
    length = len(eventhub_configs)
    print(f"\n--- CREATING {length} EVENT HUB CONSUMER CLIENTS ---\n")

    start_transform_scheduler(SECONDS_BETWEEN_RAW_TO_MEASUREMENTS_TRANSFORM)
    start_consumers(eventhub_configs)


if __name__ == "__main__":
    main()
