-- AICODE-NOTE: Reset database schema safely for local development
-- This script drops and recreates the public schema and required extensions.

-- AICODE-NOTE: Never run this in production. Intended for dev-only resets.

BEGIN;

-- Drop and recreate public schema
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA IF NOT EXISTS public;
GRANT ALL ON SCHEMA public TO public;

-- Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()

COMMIT;


