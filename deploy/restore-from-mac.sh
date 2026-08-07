#!/usr/bin/env sh
set -eu

. deploy/load-env.sh

BACKUP_DIR="${1:?Usage: deploy/restore-from-mac.sh backup/cloud/YYYYMMDD_HHMMSS}"
PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"
TIMESTAMP="$(basename "$BACKUP_DIR")"

gcloud config set project "$PROJECT_ID" >/dev/null

case "$TIMESTAMP" in
  [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]) ;;
  *) echo "Backup directory must end with YYYYMMDD_HHMMSS." >&2; exit 1 ;;
esac

test -s "$BACKUP_DIR/database.dump"
test -s "$BACKUP_DIR/files.tar.gz"
if [ -f "$BACKUP_DIR/SHA256SUMS" ]; then
  (cd "$BACKUP_DIR" && shasum -a 256 -c SHA256SUMS)
fi

PROJECT_ID="$PROJECT_ID" ZONE="$ZONE" VM_NAME="$VM_NAME" sh deploy/start.sh
gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command "sudo rm -rf '/opt/solomon/backups/$TIMESTAMP'"
gcloud compute scp --recurse "$BACKUP_DIR" "$VM_NAME:/tmp/" --zone "$ZONE"
gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command \
  "sudo mv '/tmp/$TIMESTAMP' /opt/solomon/backups/ && sudo chown -R solomon:solomon '/opt/solomon/backups/$TIMESTAMP' && sudo -u solomon sh -c 'cd /opt/solomon && sh deploy/restore.sh $TIMESTAMP'"
gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command "sudo rm -rf '/opt/solomon/backups/$TIMESTAMP'"
echo "Restore complete from $BACKUP_DIR"