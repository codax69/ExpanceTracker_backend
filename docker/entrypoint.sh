#!/bin/bash
# docker/entrypoint.sh — waits for MySQL then runs migrations and starts server

set -e

# ── Wait for MySQL to be ready ────────────────────────────────────────────────
echo "⏳ Waiting for MySQL at ${MYSQL_HOST}:${MYSQL_PORT:-3306}..."
while ! nc -z "${MYSQL_HOST}" "${MYSQL_PORT:-3306}"; do
  sleep 1
done
echo "✅ MySQL is up!"

# ── Apply migrations ──────────────────────────────────────────────────────────
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# ── Collect static files ──────────────────────────────────────────────────────
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# ── Execute the main container command (gunicorn / dev server) ────────────────
exec "$@"
