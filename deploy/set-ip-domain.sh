#!/usr/bin/env sh
# Fetch the VM's current external IP, derive a sslip.io hostname, update
# deploy/production.env, and restart Caddy on the VM so the new certificate
# is obtained automatically.
#
# Usage (from repo root):
#   sh deploy/set-ip-domain.sh
#
# Prerequisites: PROJECT_ID, ZONE, VM_NAME must be set (or rely on defaults).
set -eu

. deploy/load-env.sh

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"
ENV_FILE="$(dirname "$0")/production.env"

gcloud config set project "$PROJECT_ID" >/dev/null

state="$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" --format='value(status)')"
if [ "$state" != RUNNING ]; then
  echo "VM $VM_NAME is not running (state: $state). Start it first." >&2
  exit 1
fi

external_ip="$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" \
  --format='value(networkInterfaces[0].accessConfigs[0].natIP)')"

if [ -z "$external_ip" ]; then
  echo "Could not retrieve external IP for $VM_NAME." >&2
  exit 1
fi

# Convert dots to dashes for sslip.io, e.g. 35.246.161.220 -> 35-246-161-220.sslip.io
ip_dashes="$(echo "$external_ip" | tr '.' '-')"
domain="${ip_dashes}.sslip.io"

echo "External IP : $external_ip"
echo "New DOMAIN  : $domain"

# Update DOMAIN, ALLOWED_HOSTS in deploy/production.env using sed
sed -i.bak \
  -e "s|^DOMAIN=.*|DOMAIN=${domain}|" \
  -e "s|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${domain}|" \
  "$ENV_FILE"
rm -f "${ENV_FILE}.bak"

echo "Updated $ENV_FILE"

# Check whether .env.production already exists on the VM (created by release.sh).
env_exists="$(gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command \
  "test -f /opt/solomon/.env.production && echo yes || echo no" 2>/dev/null || echo no)"

if [ "$env_exists" = yes ]; then
  # Patch DOMAIN/ALLOWED_HOSTS in place, preserving secrets appended by remote-update.sh,
  # then restart only Caddy to pick up the new hostname.
  gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command \
    "sudo -u solomon sh -c \"sed -i -e 's|^DOMAIN=.*|DOMAIN=${domain}|' -e 's|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${domain}|' /opt/solomon/.env.production\" && sudo -u solomon sh -c 'cd /opt/solomon && docker compose --env-file .env.production -f docker-compose.production.yml up -d --no-deps caddy'"
  echo ""
  echo "Done. Solomon will be available at https://${domain} once Caddy obtains its certificate (up to 60 s)."
else
  echo ""
  echo "No .env.production found on the VM - this is the first deployment."
  echo "deploy/production.env has been updated. Run the first release next:"
  echo ""
  echo "  export NETBOX_VERSION=v4.5.8"
  echo "  sh deploy/release.sh"
fi
