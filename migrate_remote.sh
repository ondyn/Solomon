#!/usr/bin/env sh

set -eu

. deploy/load-env.sh

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"
REMOTE_COMPOSE="sh deploy/compose.sh --env-file .env.production -f docker-compose.production.yml"

command -v gcloud >/dev/null 2>&1 || {
  echo "Google Cloud CLI is required." >&2
  exit 1
}

gcloud config set project "$PROJECT_ID" >/dev/null

echo "Starting the target VM if necessary..."
PROJECT_ID="$PROJECT_ID" ZONE="$ZONE" VM_NAME="$VM_NAME" sh deploy/start.sh

echo "Downloading a full pre-migration backup from $VM_NAME..."
PROJECT_ID="$PROJECT_ID" ZONE="$ZONE" VM_NAME="$VM_NAME" sh deploy/backup-from-mac.sh

echo "Current migration state:"
gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command \
  "sudo -u solomon sh -c 'cd /opt/solomon && $REMOTE_COMPOSE exec -T netbox python manage.py showmigrations --plan'"

echo "Applying all migrations..."
gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command \
  "sudo -u solomon sh -c 'cd /opt/solomon && $REMOTE_COMPOSE exec -T netbox python manage.py migrate --no-input'"

PROJECT_ID="$PROJECT_ID" ZONE="$ZONE" VM_NAME="$VM_NAME" sh deploy/status.sh
echo "Remote migrations complete."