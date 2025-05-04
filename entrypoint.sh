#!/bin/bash

set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h db -p 5432 -U "$POSTGRES_USER"; do
  sleep 1
done
echo "PostgreSQL is ready."

if [ ! -d "migrations" ]; then
  echo "No migrations folder found. Initializing..."
  flask db init
fi

echo "Generating migrations if needed..."
flask db migrate -m "Auto migration" || echo "No changes detected."

echo "Applying migrations..."
flask db upgrade

echo "Starting Flask..."
exec flask run --host=0.0.0.0 --port=5000
