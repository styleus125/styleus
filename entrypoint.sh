#!/bin/sh
set -e

echo "Running database migrations..."
flask db upgrade 2>/dev/null || python -c "from app import app; from models import db; app.app_context().push(); db.create_all(); print('Tables created.')"

echo "Seeding default data..."
flask seed 2>/dev/null || true

echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 "app:app"
