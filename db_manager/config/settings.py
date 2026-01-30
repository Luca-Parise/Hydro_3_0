import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DB_HOST = os.getenv("PGHOST", "localhost")
DB_PORT = int(os.getenv("PGPORT", "5432"))
DB_NAME = os.getenv("PGDBNAME", "messages_trebisacce")
DB_USER = os.getenv("PGUSER", "postgres")
DB_PASSWORD = os.getenv("PGPASSWORD", "")

# Ingestion pacing
HEARTBEAT_SECONDS = int(os.getenv("HEARTBEAT_SECONDS", "60"))
MIN_SECONDS_BETWEEN_EVENTS = 900  # 15 minutes

# Scheduler intervals (seconds)
SECONDS_BETWEEN_RAW_TO_MEASUREMENTS_TRANSFORM = 900  # 15 minutes
SECONDS_BETWEEN_CLEAN_MEASUREMENTS = 300  # 5 minutes
SECONDS_BETWEEN_REFRESH_STATS = 86400  # 24 hours
SECONDS_BETWEEN_REFRESH_MV = 86400  # 24 hours

# Tables
RAW_TABLE_NAME = "hydro.tab_measurements_raw"

# Hampel filter parameters
HAMPEL_WINDOW_SIZE = 100
HAMPEL_SIGMA_THRESHOLD = 3.5

