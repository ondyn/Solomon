#!/usr/bin/env sh
set -eu

. deploy/load-env.sh

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"
BACKUP_FIRST="${BACKUP_FIRST:-false}"

gcloud config set project "$PROJECT_ID" >/dev/null

if [ "${1:-}" = "--backup" ]; then
  BACKUP_FIRST=true
fi

if [ "$BACKUP_FIRST" = true ]; then
  PROJECT_ID="$PROJECT_ID" ZONE="$ZONE" VM_NAME="$VM_NAME" sh deploy/backup-from-mac.sh
fi

state="$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" --format='value(status)')"
if [ "$state" = TERMINATED ]; then
  echo "$VM_NAME is already stopped."
  exit 0
fi

echo "Stopping $VM_NAME gracefully..."
gcloud compute instances stop "$VM_NAME" --zone "$ZONE" --quiet
echo "VM compute charges are stopped. Persistent disk and stored artifacts still incur small charges."