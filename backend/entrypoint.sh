#!/bin/bash
set -e

echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations completed."

echo "Starting the server..."

# If SERVER_RELOAD is set, you can let docker-compose command handle --reload.
if [ "$SERVER_RELOAD" = "True" ] || [ "$SERVER_RELOAD" = "true" ]; then
  exec uvicorn app.server:app --host "${SERVER_HOST:-0.0.0.0}" --port "${SERVER_PORT:-8000}" --reload
fi

exec gunicorn app.server:app -k uvicorn.workers.UvicornWorker -c /backend/app/gunicorn.conf.py