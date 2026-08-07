#!/usr/bin/env sh

set -eu

BACKUP_DIR="./backup"
INPUT_BACKUP="${1:-}"

if [ "$#" -gt 1 ]; then
  echo "Usage: $0 [DUMP_FILE|TIMESTAMP]" >&2
  exit 1
fi

if [ -n "$INPUT_BACKUP" ] && [ -f "$INPUT_BACKUP" ]; then
  BACKUP_FILE="$INPUT_BACKUP"
elif [ -n "$INPUT_BACKUP" ]; then
  case "$INPUT_BACKUP" in
    */*|*.dump)
      echo "Backup file not found: $INPUT_BACKUP" >&2
      exit 1
      ;;
  esac

  BACKUP_FILE="${BACKUP_DIR}/db_backup_${INPUT_BACKUP}.dump"
  if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found for timestamp: $INPUT_BACKUP" >&2
    echo "Expected: $BACKUP_FILE" >&2
    exit 1
  fi
elif [ ! -d "$BACKUP_DIR" ]; then
  echo "Backup directory not found: $BACKUP_DIR" >&2
  exit 1
else
  BACKUP_FILE="$(ls -1t "${BACKUP_DIR}"/db_backup_*.dump 2>/dev/null | head -n 1 || true)"
  if [ -z "$BACKUP_FILE" ]; then
    echo "No backup files found in $BACKUP_DIR" >&2
    exit 1
  fi
fi

echo "Using backup file: $BACKUP_FILE"
echo "Validating backup file..."
docker compose exec -T postgres pg_restore --list < "$BACKUP_FILE" >/dev/null

echo "Stopping NetBox while restoring..."
docker compose stop netbox netbox-worker

echo "Dropping and recreating database, then restoring data..."

docker compose exec -T postgres sh -c '
  dropdb -U "$POSTGRES_USER" --if-exists --force "$POSTGRES_DB" &&
  createdb -U "$POSTGRES_USER" "$POSTGRES_DB" &&
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --exit-on-error --no-owner --no-privileges
' < "$BACKUP_FILE"

docker compose up -d netbox netbox-worker

echo "Restore complete from: $BACKUP_FILE"