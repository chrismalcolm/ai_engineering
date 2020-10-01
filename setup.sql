CREATE USER testuser WITH encrypted password 'pass123';
GRANT all privileges ON DATABASE postgres TO testuser;

CREATE TABLE IF NOT EXISTS metrics (
	id SERIAL PRIMARY KEY,
    cpu_load REAL,
	concurrency INTEGER,
    timestamp INTEGER
);

GRANT all privileges ON TABLE metrics TO testuser;
GRANT all privileges ON TABLE metrics_id_seq TO testuser;
