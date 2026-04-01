#!/bin/bash
####
## Solomon - Docker Entrypoint
##
## Based on the upstream NetBox Docker entrypoint but with Solomon-specific
## changes to handle disabled modules (DCIM, Circuits, IPAM, etc.).
##
## Changes from upstream:
##   - trace_paths is skipped (DCIM tables may not exist)
##   - reindex uses --lazy to avoid querying disabled-app tables
####

# Stop when an error occures
set -e

# Allows NetBox to be run as non-root users
umask 002

# Load correct Python3 env
# shellcheck disable=SC1091
source /opt/netbox/venv/bin/activate

# Try to connect to the DB
DB_WAIT_TIMEOUT=${DB_WAIT_TIMEOUT-3}
MAX_DB_WAIT_TIME=${MAX_DB_WAIT_TIME-30}
CUR_DB_WAIT_TIME=0
while [ "${CUR_DB_WAIT_TIME}" -lt "${MAX_DB_WAIT_TIME}" ]; do
  # Read and truncate connection error tracebacks to last line by default
  exec {psfd}< <(./manage.py showmigrations 2>&1)
  read -rd '' DB_ERR <&$psfd || :
  exec {psfd}<&-
  wait $! && break
  if [ -n "$DB_WAIT_DEBUG" ]; then
    echo "$DB_ERR"
  else
    readarray -tn 0 DB_ERR_LINES <<<"$DB_ERR"
    echo "${DB_ERR_LINES[@]: -1}"
    echo "[ Use DB_WAIT_DEBUG=1 in netbox.env to print full traceback for errors here ]"
  fi
  echo "⏳ Waiting on DB... (${CUR_DB_WAIT_TIME}s / ${MAX_DB_WAIT_TIME}s)"
  sleep "${DB_WAIT_TIMEOUT}"
  CUR_DB_WAIT_TIME=$((CUR_DB_WAIT_TIME + DB_WAIT_TIMEOUT))
done
if [ "${CUR_DB_WAIT_TIME}" -ge "${MAX_DB_WAIT_TIME}" ]; then
  echo "❌ Waited ${MAX_DB_WAIT_TIME}s or more for the DB to become ready."
  exit 1
fi
# Check if update is needed
if ! ./manage.py migrate --check >/dev/null 2>&1; then
  echo "⚙️ Applying database migrations"
  ./manage.py migrate --no-input
  # trace_paths is a DCIM management command — skip it when DCIM tables
  # don't exist (Solomon disables DCIM migrations).
  echo "⚙️ Skipping trace_paths (DCIM disabled)"
  # remove_stale_contenttypes tries to CASCADE-delete ContentType entries
  # for disabled apps, which queries their (non-existent) tables.
  # Skip it — stale content types for disabled apps are harmless.
  echo "⚙️ Skipping remove_stale_contenttypes (disabled apps have no tables)"
  echo "⚙️ Removing expired user sessions"
  ./manage.py clearsessions
  echo "⚙️ Building search index (lazy)"
  ./manage.py reindex --lazy || echo "⚠️ reindex failed (non-fatal, some disabled-app tables missing)"
fi

# Create Superuser if required
if [ "$SKIP_SUPERUSER" == "true" ]; then
  echo "↩️ Skip creating the superuser"
else
  ./manage.py shell --no-startup --no-imports --interface python \
    </opt/netbox/super_user.py
fi

echo "✅ Initialisation is done."

# Launch whatever is passed by docker
# (i.e. the RUN instruction in the Dockerfile)
exec "$@"
