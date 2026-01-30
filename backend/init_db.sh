#!/bin/bash
set -e

echo "========================================="
echo "Video to Book - Database Initialization"
echo "========================================="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up and running!"

# Run Alembic migrations
echo "Running database migrations..."
cd /app

# Check if this is the first run (no migrations yet)
if [ ! "$(ls -A /app/alembic/versions/*.py 2>/dev/null)" ]; then
  echo "No migrations found. Creating initial migration..."
  alembic revision --autogenerate -m "Initial migration - create all tables"
fi

# Apply all pending migrations
echo "Applying migrations..."
alembic upgrade head

echo "Database migrations completed successfully!"
echo "========================================="

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
