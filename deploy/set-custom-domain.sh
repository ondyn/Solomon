#!/usr/bin/env sh
# Update deploy/production.env and the running VM to use a custom domain.
# The VM must be running. DNS must already point to the VM's external IP
# before running this script (Caddy needs the A record to obtain a certificate).
#
# Usage (from repo root):
#   export DOMAIN=solo-mon.site
#   sh deploy/set-custom-domain.sh
#
# Or pass the domain as the first argument:
#   sh deploy/set-custom-domain.sh solo-mon.site
#
# Prerequisites: PROJECT_ID, ZONE, VM_NAME must be set.
set -eu

. deploy/load-env.sh

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"
ENV_FILE="$(dirname "$0")/production.env"

DOMAIN="${1:-${DOMAIN:?Set DOMAIN env var or pass it as the first argument}}"

gcloud config set project "$PROJECT_ID" >/dev/null

state="$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" --format='value(status)')"
if [ "$state" != RUNNING ]; then
  echo "VM $VM_NAME is not running (state: $state). Start it first with: sh deploy/start.sh" >&2
  exit 1
fi

external_ip="$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" \
  --format='value(networkInterfaces[0].accessConfigs[0].natIP)')"

echo "VM external IP : $external_ip"
echo "Custom domain  : $DOMAIN"
echo ""
echo "Make sure the following DNS A record is set at your registrar:"
echo "  Name: @  (or solo-mon.site)   TTL: 300   Type: A   Data: $external_ip"
echo ""

# Update DOMAIN, ALLOWED_HOSTS, and ACME_EMAIL in deploy/production.env
ACME_EMAIL="${ACME_EMAIL:-}"
sed -i.bak \
  -e "s|^DOMAIN=.*|DOMAIN=${DOMAIN}|" \
  -e "s|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${DOMAIN}|" \
  "$ENV_FILE"
rm -f "${ENV_FILE}.bak"

if [ -n "$ACME_EMAIL" ]; then
  sed -i.bak -e "s|^ACME_EMAIL=.*|ACME_EMAIL=${ACME_EMAIL}|" "$ENV_FILE"
  rm -f "${ENV_FILE}.bak"
fi

echo "Updated $ENV_FILE"

# Check whether .env.production already exists on the VM
env_exists="$(gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command \
  "test -f /opt/solomon/.env.production && echo yes || echo no" 2>/dev/null || echo no)"

if [ "$env_exists" = yes ]; then
  # Patch DOMAIN/ALLOWED_HOSTS in place on the VM, then restart Caddy
  gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command \
    "sudo -u solomon sh -c \"sed -i -e 's|^DOMAIN=.*|DOMAIN=${DOMAIN}|' -e 's|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${DOMAIN}|' /opt/solomon/.env.production\" && sudo -u solomon sh -c 'cd /opt/solomon && sh deploy/compose.sh --env-file .env.production -f docker-compose.production.yml up -d --no-deps caddy'"
  echo ""
  echo "Done. Solomon will be available at https://${DOMAIN} once Caddy obtains"
  echo "its certificate (up to 60 s after DNS propagates to the VM)."
else
  echo ""
  echo "No .env.production found on the VM - this is the first deployment."
  echo "deploy/production.env has been updated. Run the first release next:"
  echo ""
  echo "  export NETBOX_VERSION=v4.5.8"
  echo "  sh deploy/release.sh"
fi
