#!/usr/bin/env sh
set -eu

. deploy/load-env.sh

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID in .env or export an existing Google Cloud project}"
REGION="${REGION:-europe-west3}"
ZONE="${ZONE:-europe-west3-a}"
VM_NAME="${VM_NAME:-solomon}"
SERVICE_ACCOUNT="solomon-runtime@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "$PROJECT_ID"
gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com compute.googleapis.com dns.googleapis.com iam.googleapis.com secretmanager.googleapis.com

gcloud artifacts repositories describe solomon-images --location "$REGION" >/dev/null 2>&1 || gcloud artifacts repositories create solomon-images --repository-format docker --location "$REGION" --description "Solomon NetBox images"
gcloud artifacts repositories describe solomon-python --location "$REGION" >/dev/null 2>&1 || gcloud artifacts repositories create solomon-python --repository-format python --location "$REGION" --description "Solomon plugin wheels"

create_secret() {
  secret_name="$1"
  secret_value="$2"
  if ! gcloud secrets describe "$secret_name" >/dev/null 2>&1; then
    printf '%s' "$secret_value" | gcloud secrets create "$secret_name" --data-file=-
  fi
}

DB_PASSWORD="$(openssl rand -hex 32)"
create_secret solomon-db-password "$DB_PASSWORD"
create_secret solomon-secret-key "$(openssl rand -hex 48)"
create_secret solomon-redis-password "$(openssl rand -hex 32)"
create_secret solomon-redis-cache-password "$(openssl rand -hex 32)"
gcloud iam service-accounts describe "$SERVICE_ACCOUNT" >/dev/null 2>&1 || gcloud iam service-accounts create solomon-runtime --display-name "Solomon runtime"
for role in roles/artifactregistry.reader roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:$SERVICE_ACCOUNT" --role "$role" --quiet >/dev/null
done

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
for role in roles/artifactregistry.writer roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" --role "$role" --quiet >/dev/null
done

if gcloud compute firewall-rules describe solomon-allow-web >/dev/null 2>&1; then
  gcloud compute firewall-rules update solomon-allow-web --rules tcp:80,tcp:443,udp:443 --source-ranges 0.0.0.0/0 --target-tags http-server,https-server
else
  gcloud compute firewall-rules create solomon-allow-web --network default --direction ingress --action allow --rules tcp:80,tcp:443,udp:443 --source-ranges 0.0.0.0/0 --target-tags http-server,https-server
fi

if ! gcloud compute instances describe "$VM_NAME" --zone "$ZONE" >/dev/null 2>&1; then
  gcloud compute instances create "$VM_NAME" --zone "$ZONE" --machine-type e2-medium --boot-disk-size 30GB --boot-disk-type pd-standard --image-family debian-12 --image-project debian-cloud --service-account "$SERVICE_ACCOUNT" --scopes cloud-platform --tags http-server,https-server --metadata-from-file startup-script=deploy/startup.sh
else
  gcloud compute instances add-metadata "$VM_NAME" --zone "$ZONE" --metadata-from-file startup-script=deploy/startup.sh
  machine_type="$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" --format='value(machineType.basename())')"
  if [ "$machine_type" != e2-medium ]; then
    state="$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" --format='value(status)')"
    if [ "$state" != TERMINATED ]; then
      echo "Stop $VM_NAME before resizing it from $machine_type to e2-medium." >&2
      echo "PROJECT_ID=$PROJECT_ID ZONE=$ZONE sh deploy/stop.sh" >&2
      exit 1
    fi
    gcloud compute instances set-machine-type "$VM_NAME" --zone "$ZONE" --machine-type e2-medium
  fi
fi

echo "Provisioning complete: $VM_NAME (e2-medium with local PostgreSQL)."
echo "Set DOMAIN DNS to the VM external IP before the first release."