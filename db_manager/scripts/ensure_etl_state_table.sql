CREATE TABLE IF NOT EXISTS hydro.tab_etl_state (
    job_name TEXT PRIMARY KEY,
    last_parent_timestampmsec BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);