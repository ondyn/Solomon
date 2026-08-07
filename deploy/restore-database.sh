#!/usr/bin/env sh

set -eu

DUMP_FILE="${1:?Usage: deploy/restore-database.sh DUMP_FILE}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"

test -s "$DUMP_FILE"

echo "Validating database dump..."
sh deploy/compose.sh --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres \
  pg_restore --list < "$DUMP_FILE" >/dev/null

echo "Dropping and recreating the database..."
sh deploy/compose.sh --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres sh -c '
  dropdb -U "$POSTGRES_USER" --if-exists --force "$POSTGRES_DB" &&
  createdb -U "$POSTGRES_USER" "$POSTGRES_DB" &&
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --exit-on-error --no-owner --no-privileges
' < "$DUMP_FILE"

echo "Database restore complete."