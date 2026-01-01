-- Weather Database Initialization Script
-- Creates the weather_data table with proper indexes

-- Create weather_data table
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    temperature FLOAT NOT NULL,
    humidity FLOAT,
    pressure FLOAT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_weather_city_country ON weather_data(city, country);
CREATE INDEX IF NOT EXISTS idx_weather_city_country_timestamp ON weather_data(city, country, timestamp DESC);

-- Create read-only user for Grafana (optional)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'grafana_reader') THEN
        CREATE ROLE grafana_reader WITH LOGIN PASSWORD 'grafana_readonly';
    END IF;
END
$$;

-- Grant read-only permissions to grafana_reader
GRANT CONNECT ON DATABASE weather_db TO grafana_reader;
GRANT USAGE ON SCHEMA public TO grafana_reader;
GRANT SELECT ON weather_data TO grafana_reader;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO grafana_reader;

-- Display table info
\d weather_data
