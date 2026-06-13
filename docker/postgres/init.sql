-- GymOS PostgreSQL initialization
-- Extensions (Alembic migrations handle tables)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Set timezone
SET timezone = 'Asia/Riyadh';
