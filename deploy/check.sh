#!/usr/bin/env sh

set -eu

ROOT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

RUFF_IMAGE="${RUFF_IMAGE:-ghcr.io/astral-sh/ruff:0.12.7-alpine}"

echo "Checking Python lint..."
docker run --rm -v "$ROOT_DIR:/workspace" -w /workspace "$RUFF_IMAGE" \
  ruff check plugins/solomon_theme plugins/solomon_property plugins/solomon_meetings

echo "Checking Python formatting..."
docker run --rm -v "$ROOT_DIR:/workspace" -w /workspace "$RUFF_IMAGE" \
  ruff format --check plugins/solomon_theme plugins/solomon_property plugins/solomon_meetings

echo "Building production image..."
sh deploy/compose.sh -f docker-compose.yml -f deploy/docker-compose.test.yml build netbox

echo "Running plugin tests..."
KEEPDB_FLAG=""
if [ "${KEEPDB:-0}" = "1" ]; then
  KEEPDB_FLAG="--keepdb"
fi
sh deploy/compose.sh -f docker-compose.yml -f deploy/docker-compose.test.yml run --rm netbox \
  /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py test \
  solomon_property.tests solomon_meetings.tests $KEEPDB_FLAG

echo "All checks passed."