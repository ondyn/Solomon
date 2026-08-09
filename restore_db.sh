#!/usr/bin/env sh

set -eu

BACKUP_ROOT="./backup/local"
INPUT_BACKUP="${1:-}"
FILES_ARCHIVE=""

if [ "$#" -gt 1 ]; then
  echo "Usage: $0 [DUMP_FILE|TIMESTAMP]" >&2
  exit 1
fi

if [ -n "$INPUT_BACKUP" ] && [ -d "$INPUT_BACKUP" ]; then
  BACKUP_FILE="$INPUT_BACKUP/database.dump"
  FILES_ARCHIVE="$INPUT_BACKUP/files.tar.gz"
elif [ -n "$INPUT_BACKUP" ] && [ -f "$INPUT_BACKUP" ]; then
  BACKUP_FILE="$INPUT_BACKUP"
elif [ -n "$INPUT_BACKUP" ]; then
  case "$INPUT_BACKUP" in
    */*|*.dump)
      echo "Backup file not found: $INPUT_BACKUP" >&2
      exit 1
      ;;
  esac

  FULL_BACKUP_DIR="${BACKUP_ROOT}/${INPUT_BACKUP}"
  if [ -d "$FULL_BACKUP_DIR" ]; then
    BACKUP_FILE="$FULL_BACKUP_DIR/database.dump"
    FILES_ARCHIVE="$FULL_BACKUP_DIR/files.tar.gz"
  else
    BACKUP_FILE="./backup/db_backup_${INPUT_BACKUP}.dump"
    if [ ! -f "$BACKUP_FILE" ]; then
      echo "Backup not found for timestamp: $INPUT_BACKUP" >&2
      echo "Expected $FULL_BACKUP_DIR or $BACKUP_FILE" >&2
      exit 1
    fi
  fi
elif [ ! -d "$BACKUP_ROOT" ]; then
  echo "Backup directory not found: $BACKUP_ROOT" >&2
  exit 1
else
  FULL_BACKUP_DIR="$(ls -1dt "${BACKUP_ROOT}"/*/ 2>/dev/null | head -n 1 || true)"
  if [ -z "$FULL_BACKUP_DIR" ]; then
    echo "No full backups found in $BACKUP_ROOT" >&2
    exit 1
  fi
  BACKUP_FILE="${FULL_BACKUP_DIR%/}/database.dump"
  FILES_ARCHIVE="${FULL_BACKUP_DIR%/}/files.tar.gz"
fi

echo "Using backup file: $BACKUP_FILE"
test -s "$BACKUP_FILE"
echo "Validating backup file..."
docker compose exec -T postgres pg_restore --list < "$BACKUP_FILE" >/dev/null

if [ -n "$FILES_ARCHIVE" ]; then
  test -s "$FILES_ARCHIVE"
  BACKUP_DIRECTORY="$(dirname "$BACKUP_FILE")"
  if [ -f "$BACKUP_DIRECTORY/SHA256SUMS" ]; then
    (cd "$BACKUP_DIRECTORY" && shasum -a 256 -c SHA256SUMS)
  fi
  tar -tzf "$FILES_ARCHIVE" >/dev/null
  UNEXPECTED_PATHS="$(tar -tzf "$FILES_ARCHIVE" | grep -Ev '^(media|reports|scripts)(/.*)?$' || true)"
  if [ -n "$UNEXPECTED_PATHS" ]; then
    echo "File archive contains unexpected paths:" >&2
    printf '%s\n' "$UNEXPECTED_PATHS" >&2
    exit 1
  fi
else
  echo "Warning: legacy database-only backup; persistent files will not be changed." >&2
fi

echo "Stopping NetBox while restoring..."
docker compose stop netbox netbox-worker

echo "Dropping and recreating database, then restoring data..."

docker compose exec -T postgres sh -c '
  dropdb -U "$POSTGRES_USER" --if-exists --force "$POSTGRES_DB" &&
  createdb -U "$POSTGRES_USER" "$POSTGRES_DB" &&
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --exit-on-error --no-owner --no-privileges
' < "$BACKUP_FILE"

if [ -n "$FILES_ARCHIVE" ]; then
  echo "Restoring persistent files..."
  ARCHIVE_DIRECTORY="$(CDPATH='' cd -- "$(dirname "$FILES_ARCHIVE")" && pwd)"
  ARCHIVE_NAME="$(basename "$FILES_ARCHIVE")"
  docker compose run --rm -v "$ARCHIVE_DIRECTORY:/restore:ro" volume-tools \
    sh -c "find /data/media /data/reports /data/scripts -mindepth 1 -delete && tar -xzf '/restore/$ARCHIVE_NAME' -C /data"
fi

docker compose up -d netbox netbox-worker

echo "Restore complete from: $BACKUP_FILE"