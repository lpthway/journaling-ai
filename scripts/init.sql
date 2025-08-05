-- PostgreSQL Initialization Script for Journaling AI
-- This script sets up the database with proper configuration

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Set timezone
SET timezone = 'UTC';

-- Create application user (optional, for production)
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'journaling_user') THEN
--         CREATE USER journaling_user WITH PASSWORD 'secure_password';
--         GRANT CONNECT ON DATABASE journaling_ai TO journaling_user;
--         GRANT USAGE ON SCHEMA public TO journaling_user;
--         GRANT CREATE ON SCHEMA public TO journaling_user;
--     END IF;
-- END
-- $$;

-- Performance tuning for development
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Restart required for some settings, but this gives us a good starting point
SELECT 'Database initialized successfully' AS status;
