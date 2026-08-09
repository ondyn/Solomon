#!/usr/bin/env sh

set -eu

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"
TIMESTAMP="${1:-$(date -u +%Y%m%d_%H%M%S)}"
BACKUP_DIR="backups/$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

attempt=0
until sh deploy/compose.sh --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres \
  sh -c 'pg_isready -q -d "$POSTGRES_DB" -U "$POSTGRES_USER"'; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    echo "PostgreSQL did not become ready for backup." >&2
    exit 1
  fi
  sleep 2
done

echo "Backing up PostgreSQL..."
sh deploy/compose.sh --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > "$BACKUP_DIR/database.dump"

echo "Backing up persistent files..."
sh deploy/compose.sh --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm volume-tools \
  tar -czf "/backups/$TIMESTAMP/files.tar.gz" -C /data media reports scripts

printf '%s\n' "$TIMESTAMP" > "$BACKUP_DIR/manifest.txt"
sh deploy/compose.sh --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres \
  pg_restore --list < "$BACKUP_DIR/database.dump" >/dev/null
tar -tzf "$BACKUP_DIR/files.tar.gz" >/dev/null
echo "Backup ready at $BACKUP_DIR"