CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes that will be used frequently
-- (tables created by SQLAlchemy/Alembic on first run)
