import threading
from time import time, sleep
import json
import traceback

import psycopg2
from azure.eventhub import EventHubConsumerClient

from db_manager.config.settings import MIN_SECONDS_BETWEEN_EVENTS, RAW_TABLE_NAME
from db_manager.db.conn import get_conn
from db_manager.db.sql_loader import load_sql

LAST_EVENT_TS_BY_ID = {}
STATE_LOCK = threading.Lock()

"""
NOTE (problemi aperti / possibili miglioramenti):
- La connessione DB viene aperta per ogni evento: su carichi continui aumenta latenza e rischio di saturare il DB.
- Il retry e' minimo (1 solo tentativo con 1s fisso): se il DB ha un guasto temporaneo si perdono eventi.
- Il checkpoint si aggiorna solo dopo insert riuscito: se fallisce l'insert l'evento viene riprocessato in loop.
- LAST_EVENT_TS_BY_ID cresce senza limiti: con molti device nel tempo puo' consumare RAM (serve TTL/eviction).
- I consumer sono thread daemon: in uscita non c'e' uno shutdown pulito, quindi close/checkpoint non garantiti.
- La validazione del payload e' minima: dati malformati passano silenziosamente, difficile fare debug.
"""


def load_eventhub_configs():
    eventhub_configs = []
    try:
        with get_conn() as conn:
            sql = load_sql("select_eventhub_configs.sql")
            with conn.cursor() as cur:
                cur.execute(sql)
                misuratori = cur.fetchall()
                for id_misuratore, name, eventhub_connection_string, eventhub_consumer_group in misuratori:
                    eventhub_configs.append({
                        "id_misuratore": id_misuratore,
                        "name": name,
                        "eventhub_connection_string": eventhub_connection_string,
                        "eventhub_consumer_group": eventhub_consumer_group,
                    })
    except Exception as e:
        print(f"Error retrieving misuratori: {e}")
        raise

    return eventhub_configs


def on_event(partition_context, event):
    try:
        payload = json.loads(event.body_as_str())
    except Exception as e:
        print(f"[on_event] JSON error: {e}")
        return

    current_ts = time()

    values = payload.get("values", {})
    if not isinstance(values, dict):
        return
    group_name = payload.get("group_name", "")
    parent_timestamp = payload.get("timestamp")
    parent_timestampMsec = payload.get("timestampMsec")

    params = []
    for device_id, gateway in values.items():
        with STATE_LOCK:
            last_ts = LAST_EVENT_TS_BY_ID.get(device_id, 0.0)
            elapsed = current_ts - last_ts
        if elapsed < MIN_SECONDS_BETWEEN_EVENTS:
            continue
        with STATE_LOCK:
            LAST_EVENT_TS_BY_ID[device_id] = current_ts
        if not isinstance(gateway, dict):
            continue
        for measure_name, measure_data in gateway.items():
            params.append((
                device_id,
                group_name,
                parent_timestamp,
                parent_timestampMsec,
                measure_name,
                measure_data.get("raw_data"),
                measure_data.get("status"),
                measure_data.get("timestamp"),
                measure_data.get("timestampMsec"),
            ))

    if not params:
        return

    # Insert rows into DB (one row per measure)
    for attempt in range(2):
        try:
            with get_conn() as conn:
                sql = load_sql("insert_raw_measurements.sql").replace("{RAW_TABLE_NAME}", RAW_TABLE_NAME)
                with conn.cursor() as cur:
                    cur.executemany(sql, params)
                conn.commit()
            print(f"[on_event] inserted {len(params)} rows")
            print(f"[on_event] waiting for next event (min {MIN_SECONDS_BETWEEN_EVENTS}s per device)...")
            break
        except psycopg2.OperationalError as e:
            print(f"[on_event] DB insert operational error: {e}")
            traceback.print_exc()
            if attempt == 0:
                sleep(1)
                continue
            return
        except Exception as e:
            print(f"[on_event] DB insert error: {e}")
            traceback.print_exc()
            return

    partition_context.update_checkpoint(event)


def run_consumer(config):
    client = None
    try:
        client = EventHubConsumerClient.from_connection_string(
            conn_str=config["eventhub_connection_string"],
            consumer_group=config["eventhub_consumer_group"]
        )
        print(f"EventHubConsumerClient created successfully for misuratore {config['id_misuratore']}.")

        with client:
            client.receive(
                on_event=on_event,
                starting_position="-1"  # Inizia dagli eventi piu recenti
            )
    except Exception as e:
        print(f"Error creating EventHubConsumerClient for misuratore {config['id_misuratore']}: {e}")
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


def start_consumers(eventhub_configs):
    threads = []
    for config in eventhub_configs:
        thread = threading.Thread(target=run_consumer, args=(config,), daemon=True)
        thread.start()
        threads.append(thread)

    print("Event Hub consumers started. Press CTRL+C to stop.")
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("Stopping consumers...")


"""
Esempio di payload (schema):
{
    "timestamp": 1769502588,
    "timestampMsec": 1769502587840,
    "group_name": "default",
    "values": {
        "Gateway 1": {
            "Return water temperature 2": {
            "raw_data": 47.75,
            "timestamp": 1769502587,
            "status": 1,
            "timestampMsec": 1769502587132
            }
        }
    }
}
"""
