#!/usr/bin/env sh

set -eu

. deploy/load-env.sh

DUMP_FILE="${1:?Usage: CONFIRM_REMOTE_RESTORE=solomon PROJECT_ID=project-id $0 DUMP_FILE}"
PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"

if [ "$#" -ne 1 ]; then
  echo "Usage: CONFIRM_REMOTE_RESTORE=solomon PROJECT_ID=project-id $0 DUMP_FILE" >&2
  exit 1
fi

if [ ! -s "$DUMP_FILE" ]; then
  echo "Dump file not found or empty: $DUMP_FILE" >&2
  exit 1
fi

if [ "${CONFIRM_REMOTE_RESTORE:-}" != solomon ]; then
  echo "Refusing to replace the remote database." >&2
  echo "Set CONFIRM_REMOTE_RESTORE=solomon after verifying the dump and target project." >&2
  exit 1
fi

command -v gcloud >/dev/null 2>&1 || {
  echo "Google Cloud CLI is required." >&2
  exit 1
}

REMOTE_ID="$(date -u +%Y%m%d_%H%M%S)_$$"
REMOTE_DUMP="/tmp/solomon-database-${REMOTE_ID}.dump"
REMOTE_HELPER="/tmp/solomon-restore-database-${REMOTE_ID}.sh"

cleanup() {
  gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command \
    "sudo rm -f '$REMOTE_DUMP' '$REMOTE_HELPER'" >/dev/null 2>&1 || true
}

gcloud config set project "$PROJECT_ID" >/dev/null

echo "Starting the target VM if necessary..."
PROJECT_ID="$PROJECT_ID" ZONE="$ZONE" VM_NAME="$VM_NAME" sh deploy/start.sh

echo "Downloading a full pre-restore backup from $VM_NAME..."
PROJECT_ID="$PROJECT_ID" ZONE="$ZONE" VM_NAME="$VM_NAME" sh deploy/backup-from-mac.sh

echo "Uploading database dump to $VM_NAME..."
trap cleanup EXIT
trap 'exit 1' HUP INT TERM
gcloud compute scp "$DUMP_FILE" "$VM_NAME:$REMOTE_DUMP" --zone "$ZONE"
gcloud compute scp deploy/restore-database.sh "$VM_NAME:$REMOTE_HELPER" --zone "$ZONE"

echo "Replacing the remote database..."
gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command \
  "sudo chown solomon:solomon '$REMOTE_DUMP' '$REMOTE_HELPER' && sudo -u solomon sh -c 'cd /opt/solomon && sh deploy/compose.sh --env-file .env.production -f docker-compose.production.yml stop netbox netbox-worker && sh \"$REMOTE_HELPER\" \"$REMOTE_DUMP\" && sh deploy/compose.sh --env-file .env.production -f docker-compose.production.yml up -d netbox netbox-worker'"

echo "Remote database restore complete. Verify the application before accepting writes."