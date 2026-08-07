#!/usr/bin/env sh
set -eu

. deploy/load-env.sh

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"
LOCAL_BACKUP_ROOT="${LOCAL_BACKUP_ROOT:-backup/cloud}"
TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
LOCAL_BACKUP_DIR="$LOCAL_BACKUP_ROOT/$TIMESTAMP"

gcloud config set project "$PROJECT_ID" >/dev/null

state="$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" --format='value(status)')"
if [ "$state" != RUNNING ]; then
  echo "$VM_NAME must be running. Start it with: PROJECT_ID=$PROJECT_ID sh deploy/start.sh" >&2
  exit 1
fi

mkdir -p "$LOCAL_BACKUP_ROOT"
echo "Creating backup $TIMESTAMP on $VM_NAME..."
gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command \
  "sudo -u solomon sh -c 'cd /opt/solomon && sh deploy/backup.sh $TIMESTAMP'"

echo "Downloading backup to $LOCAL_BACKUP_DIR..."
gcloud compute scp --recurse "$VM_NAME:/opt/solomon/backups/$TIMESTAMP" "$LOCAL_BACKUP_ROOT/" --zone "$ZONE"

test -s "$LOCAL_BACKUP_DIR/database.dump"
test -s "$LOCAL_BACKUP_DIR/files.tar.gz"
(
  cd "$LOCAL_BACKUP_DIR"
  shasum -a 256 database.dump files.tar.gz > SHA256SUMS
)

gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command "sudo rm -rf '/opt/solomon/backups/$TIMESTAMP'"
echo "Backup complete: $LOCAL_BACKUP_DIR"
echo "Keep a second copy on another disk or object-storage provider."