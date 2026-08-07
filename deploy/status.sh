#!/usr/bin/env sh
set -eu

. deploy/load-env.sh

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"

gcloud config set project "$PROJECT_ID" >/dev/null

gcloud compute instances describe "$VM_NAME" --zone "$ZONE" \
  --format='table(name,status,machineType.basename(),networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP,disks[0].diskSizeGb:label=DISK_GB)'

state="$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" --format='value(status)')"
if [ "$state" = RUNNING ]; then
  gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command \
    "sudo -u solomon sh -c 'cd /opt/solomon && sh deploy/compose.sh --env-file .env.production -f docker-compose.production.yml ps'"
fi