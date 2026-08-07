#!/usr/bin/env sh
set -eu

. deploy/load-env.sh

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
REGION="${REGION:-europe-west3}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"
NETBOX_VERSION="${NETBOX_VERSION:?Set NETBOX_VERSION}"
RELEASE_TAG="${RELEASE_TAG:-$(git rev-parse --short HEAD)}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/solomon-images/netbox:${RELEASE_TAG}"

gcloud config set project "$PROJECT_ID" >/dev/null

test -f deploy/production.env || { echo "Create deploy/production.env from the example first." >&2; exit 1; }

sh deploy/check.sh
PROJECT_ID="$PROJECT_ID" REGION="$REGION" sh deploy/publish-plugins.sh
gcloud builds submit --config deploy/cloudbuild.yaml --substitutions "_NETBOX_VERSION=$NETBOX_VERSION,_IMAGE=$IMAGE" .

PROJECT_ID="$PROJECT_ID" ZONE="$ZONE" VM_NAME="$VM_NAME" sh deploy/start.sh
tar -czf - docker-compose.production.yml docker/Caddyfile deploy/backup.sh deploy/restore.sh deploy/restore-database.sh deploy/compose.sh deploy/remote-update.sh deploy/production.env | gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command "sudo -u solomon tar -xzf - -C /opt/solomon"
gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command "sudo -u solomon sh -c 'cd /opt/solomon && sh deploy/remote-update.sh \"$IMAGE\" \"$REGION\"'"

echo "Release $RELEASE_TAG deployed."