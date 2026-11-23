#!/usr/bin/env bash
# Database and Media Restore Script for MoneyMatrix / ExpenseTracker
set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path_to_db_backup.sql.gz> [path_to_media_backup.tar.gz]"
    exit 1
fi

DB_BACKUP_FILE="$1"
MEDIA_BACKUP_FILE="${2:-}"

if [ ! -f "${DB_BACKUP_FILE}" ]; then
    echo "Error: Database backup file not found: ${DB_BACKUP_FILE}"
    exit 1
fi

echo "==> [$(date)] Restoring database from ${DB_BACKUP_FILE}..."
gunzip < "${DB_BACKUP_FILE}" | mysql \
    -h "${MYSQL_HOST:-db}" \
    -P "${MYSQL_PORT:-3306}" \
    -u "${MYSQL_USER:-expenseuser}" \
    -p"${MYSQL_PASSWORD}" \
    "${MYSQL_DATABASE}"
echo "==> Database restored successfully."

if [ -n "${MEDIA_BACKUP_FILE}" ]; then
    if [ -f "${MEDIA_BACKUP_FILE}" ]; then
        echo "==> Restoring media files into /app/media..."
        mkdir -p /app/media
        tar -xzf "${MEDIA_BACKUP_FILE}" -C /app/media
        echo "==> Media files restored successfully."
    else
        echo "Warning: Media backup file not found: ${MEDIA_BACKUP_FILE}"
    fi
fi

echo "==> [$(date)] Restore procedure completed."
