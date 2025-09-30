-- Database initialization script for AI Video Automation Pipeline
-- This script sets up the initial database structure and basic configuration

-- Create database (if not exists)
-- This is handled by Docker Compose environment variables

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Basic database setup
-- Tables will be created by Alembic migrations in Task 4

-- Create a simple health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS TABLE(status text, timestamp timestamptz) AS $$
BEGIN
    RETURN QUERY SELECT 'healthy'::text, NOW();
END;
$$ LANGUAGE plpgsql;