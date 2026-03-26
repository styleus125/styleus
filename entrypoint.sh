#!/bin/bash
set -e

echo "Running database migrations..."
flask db-init 2>/dev/null || true

echo "Seeding database..."
flask seed 2>/dev/null || echo "Seed skipped (already seeded)"

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 "app:app"
