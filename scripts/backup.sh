#!/usr/bin/env bash
# Automated Backup Script for MoneyMatrix / ExpenseTracker
# Backs up MySQL database dump and media uploads directory.
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DB_BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql.gz"
MEDIA_BACKUP_FILE="${BACKUP_DIR}/media_backup_${TIMESTAMP}.tar.gz"

mkdir -p "${BACKUP_DIR}"

echo "==> [$(date)] Starting MoneyMatrix backup..."

# 1. Backup MySQL Database
if [ -n "${MYSQL_DATABASE:-}" ] && [ -n "${MYSQL_PASSWORD:-}" ]; then
    echo "Dumping database: ${MYSQL_DATABASE}..."
    mysqldump \
        -h "${MYSQL_HOST:-db}" \
        -P "${MYSQL_PORT:-3306}" \
        -u "${MYSQL_USER:-expenseuser}" \
        -p"${MYSQL_PASSWORD}" \
        --single-transaction \
        --quick \
        "${MYSQL_DATABASE}" | gzip -9 > "${DB_BACKUP_FILE}"
    echo "Database backup saved to: ${DB_BACKUP_FILE}"
fi

# 2. Backup Media Directory
MEDIA_DIR="/app/media"
if [ -d "${MEDIA_DIR}" ]; then
    echo "Archiving media directory: ${MEDIA_DIR}..."
    tar -czf "${MEDIA_BACKUP_FILE}" -C "${MEDIA_DIR}" .
    echo "Media backup saved to: ${MEDIA_BACKUP_FILE}"
fi

# 3. Retention policy: Keep backups from last 14 days
echo "Cleaning up backups older than 14 days..."
find "${BACKUP_DIR}" -type f -name "*_backup_*.gz" -mtime +14 -delete

echo "==> [$(date)] Backup completed successfully."
