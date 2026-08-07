#!/usr/bin/env sh
set -eu

. deploy/load-env.sh

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export it}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"
DNS_ZONE="${DNS_ZONE:-}"
DOMAIN="${DOMAIN:-}"

gcloud config set project "$PROJECT_ID" >/dev/null
state="$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" --format='value(status)')"

if [ "$state" != RUNNING ]; then
  echo "Starting $VM_NAME..."
  gcloud compute instances start "$VM_NAME" --zone "$ZONE" --quiet
fi

attempt=0
until gcloud compute ssh "$VM_NAME" --zone "$ZONE" --command "test -f /var/lib/solomon-ready" >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 60 ]; then
    echo "VM bootstrap did not complete within five minutes. Check its serial-port output." >&2
    exit 1
  fi
  sleep 5
done

external_ip="$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" --format='value(networkInterfaces[0].accessConfigs[0].natIP)')"

if [ -n "$DNS_ZONE" ]; then
  if [ -z "$DOMAIN" ]; then
    echo "Set DOMAIN when DNS_ZONE is set." >&2
    exit 1
  fi
  dns_name="${DOMAIN%.}."
  if gcloud dns record-sets describe "$dns_name" --zone "$DNS_ZONE" --type A >/dev/null 2>&1; then
    gcloud dns record-sets update "$dns_name" --zone "$DNS_ZONE" --type A --ttl 300 --rrdatas "$external_ip"
  else
    gcloud dns record-sets create "$dns_name" --zone "$DNS_ZONE" --type A --ttl 300 --rrdatas "$external_ip"
  fi
  echo "Cloud DNS updated: $dns_name -> $external_ip"
else
  echo "VM external IP: $external_ip"
  echo "Update the DOMAIN A record if this IP changed, or set DNS_ZONE and DOMAIN."
fi

echo "VM is running. Docker services may need up to two minutes to become healthy."