#!/usr/bin/env sh
set -eu

. deploy/load-env.sh

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"
BACKUP_DIR="${1:?Usage: CONFIRM_DELETE=solomon deploy/destroy-runtime.sh backup/cloud/YYYYMMDD_HHMMSS}"

gcloud config set project "$PROJECT_ID" >/dev/null

if [ "${CONFIRM_DELETE:-}" != solomon ]; then
  echo "Refusing to delete. Set CONFIRM_DELETE=solomon after reading deploy/README.md." >&2
  exit 1
fi

test -s "$BACKUP_DIR/database.dump"
test -s "$BACKUP_DIR/files.tar.gz"
if [ -f "$BACKUP_DIR/SHA256SUMS" ]; then
  (cd "$BACKUP_DIR" && shasum -a 256 -c SHA256SUMS)
fi

echo "Deleting $VM_NAME and its persistent disk. Local backup: $BACKUP_DIR"
gcloud compute instances delete "$VM_NAME" --zone "$ZONE" --delete-disks all --quiet

if [ "${DELETE_ARTIFACT_REPOSITORIES:-false}" = true ]; then
  REGION="${REGION:-europe-west3}"
  gcloud artifacts repositories delete solomon-images --location "$REGION" --quiet || true
  gcloud artifacts repositories delete solomon-python --location "$REGION" --quiet || true
fi

if [ "${DELETE_SECRETS:-false}" = true ]; then
  for secret_name in solomon-db-password solomon-secret-key solomon-redis-password solomon-redis-cache-password; do
    gcloud secrets delete "$secret_name" --quiet || true
  done
fi

echo "Runtime deleted. Run provision-gcp.sh and release.sh before restoring this backup."