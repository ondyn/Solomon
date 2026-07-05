#!/usr/bin/env sh

set -eu

BACKUP_DIR="./backup"
INPUT_TIMESTAMP="${1:-}"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Backup directory not found: $BACKUP_DIR" >&2
  exit 1
fi

if [ -n "$INPUT_TIMESTAMP" ]; then
  BACKUP_FILE="${BACKUP_DIR}/db_backup_${INPUT_TIMESTAMP}.dump"
  if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found for timestamp: $INPUT_TIMESTAMP" >&2
    echo "Expected: $BACKUP_FILE" >&2
    exit 1
  fi
else
  BACKUP_FILE="$(ls -1t "${BACKUP_DIR}"/db_backup_*.dump 2>/dev/null | head -n 1 || true)"
  if [ -z "$BACKUP_FILE" ]; then
    echo "No backup files found in $BACKUP_DIR" >&2
    exit 1
  fi
fi

echo "Using backup file: $BACKUP_FILE"
echo "Dropping and recreating database, then restoring data..."

docker compose exec -T postgres sh -c '
  psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '\''$POSTGRES_DB'\'' AND pid <> pg_backend_pid();" &&
  dropdb -U "$POSTGRES_USER" --if-exists "$POSTGRES_DB" &&
  createdb -U "$POSTGRES_USER" "$POSTGRES_DB" &&
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --no-privileges
' < "$BACKUP_FILE"

echo "Restore complete from: $BACKUP_FILE"