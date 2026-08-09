#!/usr/bin/env sh
set -eu

IMAGE="${1:?Missing image URI}"
REGION="${2:?Missing Artifact Registry region}"

cd "$(dirname "$0")/.."
cp deploy/production.env .env.production

secret() { gcloud secrets versions access latest --secret "$1"; }
{
  printf '\nSOLOMON_IMAGE=%s\n' "$IMAGE"
  printf 'DB_PASSWORD=%s\n' "$(secret solomon-db-password)"
  printf 'SECRET_KEY=%s\n' "$(secret solomon-secret-key)"
  printf 'API_TOKEN_PEPPER_1=%s\n' "$(secret solomon-api-token-pepper-1)"
  printf 'REDIS_PASSWORD=%s\n' "$(secret solomon-redis-password)"
  printf 'REDIS_CACHE_PASSWORD=%s\n' "$(secret solomon-redis-cache-password)"
} >> .env.production
chmod 600 .env.production

gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

sh deploy/compose.sh --env-file .env.production -f docker-compose.production.yml pull
sh deploy/compose.sh --env-file .env.production -f docker-compose.production.yml up -d --remove-orphans

container_id="$(sh deploy/compose.sh --env-file .env.production -f docker-compose.production.yml ps --quiet netbox)"
attempt=0
while [ "$attempt" -lt 30 ]; do
  health="$(docker inspect --format '{{.State.Health.Status}}' "$container_id" 2>/dev/null || true)"
  [ "$health" = healthy ] && exit 0
  [ "$health" = unhealthy ] && break
  attempt=$((attempt + 1))
  sleep 10
done

sh deploy/compose.sh --env-file .env.production -f docker-compose.production.yml logs --tail 100 netbox
echo "Deployment did not become healthy." >&2
exit 1