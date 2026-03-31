#!/bin/bash
####
## Solomon - Dev Launch Script (with hot-reload)
##
## Replaces the default launch-netbox.sh in development:
##   - Enables granian --reload for instant restart on file changes
##   - Watches /opt/netbox/plugins_dev/ for local plugin changes
##   - debugpy is started in extra.py (set DEBUGPY_ENABLE=true in .env)
####

# Force polling mode for watchfiles to work with Docker Desktop bind mounts
# (macOS virtiofs does not reliably propagate inotify events)
export WATCHFILES_FORCE_POLLING=true

# Build reload paths as separate arguments
RELOAD_ARGS="--reload-paths /opt/netbox/netbox/"
if [ -d /opt/netbox/plugins_dev ]; then
    RELOAD_ARGS="${RELOAD_ARGS} --reload-paths /opt/netbox/plugins_dev/"
fi

exec granian \
  --host "::" \
  --port "8080" \
  --interface "wsgi" \
  --no-ws \
  --workers "${GRANIAN_WORKERS:-1}" \
  --respawn-failed-workers \
  --backpressure "${GRANIAN_BACKPRESSURE:-${GRANIAN_WORKERS:-1}}" \
  --loop "uvloop" \
  --log \
  --log-level "info" \
  --access-log \
  --working-dir "/opt/netbox/netbox/" \
  --static-path-route "/static" \
  --static-path-mount "/opt/netbox/netbox/static/" \
  --static-path-dir-to-file index.html \
  --pid-file "/tmp/granian.pid" \
  --reload \
  ${RELOAD_ARGS} \
  --reload-tick 500 \
  "netbox.granian:application"
