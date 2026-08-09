#!/usr/bin/env sh

set -eu

TIMESTAMP="${1:?Usage: deploy/restore.sh YYYYMMDD_HHMMSS}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"
BACKUP_DIR="backups/$TIMESTAMP"

test -s "$BACKUP_DIR/database.dump"
test -s "$BACKUP_DIR/files.tar.gz"

sh deploy/compose.sh --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres \
  pg_restore --list < "$BACKUP_DIR/database.dump" >/dev/null
tar -tzf "$BACKUP_DIR/files.tar.gz" >/dev/null
UNEXPECTED_PATHS="$(tar -tzf "$BACKUP_DIR/files.tar.gz" | grep -Ev '^(media|reports|scripts)(/.*)?$' || true)"
if [ -n "$UNEXPECTED_PATHS" ]; then
  echo "File archive contains unexpected paths:" >&2
  printf '%s\n' "$UNEXPECTED_PATHS" >&2
  exit 1
fi

echo "Stopping NetBox while restoring $TIMESTAMP..."
sh deploy/compose.sh --env-file "$ENV_FILE" -f "$COMPOSE_FILE" stop netbox netbox-worker

COMPOSE_FILE="$COMPOSE_FILE" ENV_FILE="$ENV_FILE" \
  sh deploy/restore-database.sh "$BACKUP_DIR/database.dump"

sh deploy/compose.sh --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm volume-tools \
  sh -c "find /data/media /data/reports /data/scripts -mindepth 1 -delete && tar -xzf /backups/$TIMESTAMP/files.tar.gz -C /data"

sh deploy/compose.sh --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d netbox netbox-worker

echo "Restore complete. Verify the application before accepting new writes."