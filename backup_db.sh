#!/usr/bin/env sh

set -eu

BACKUP_ROOT="./backup/local"
TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"

mkdir -p "$BACKUP_DIR"

echo "Backing up PostgreSQL..."
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F c' \
	> "$BACKUP_DIR/database.dump"

echo "Backing up persistent files..."
docker compose run --rm volume-tools \
	tar -czf "/backups/local/$TIMESTAMP/files.tar.gz" -C /data media reports scripts

printf '%s\n' "$TIMESTAMP" > "$BACKUP_DIR/manifest.txt"
(
	cd "$BACKUP_DIR"
	shasum -a 256 database.dump files.tar.gz > SHA256SUMS
)

echo "Validating backup..."
docker compose exec -T postgres pg_restore --list < "$BACKUP_DIR/database.dump" >/dev/null
tar -tzf "$BACKUP_DIR/files.tar.gz" >/dev/null

echo "Backup complete: $BACKUP_DIR"