#!/bin/bash
####
## Solomon - Dev Launch Script (with hot-reload)
##
## Replaces the default launch-netbox.sh in development:
##   - Enables granian --reload for instant restart on file changes
##   - Watches /opt/netbox/plugins_dev/ for local plugin changes
##   - Sends a warm-up request after start to pre-load the WSGI app
##   - debugpy is started in extra.py (set DEBUGPY_ENABLE=true in .env)
##
## Performance notes:
##   - reload-tick is set to 2000ms (2s) to reduce CPU overhead from polling
##   - Only plugins_dev is watched (NetBox core rarely changes during dev)
##   - Set WATCHFILES_FORCE_POLLING=false if your Docker setup supports inotify
##   - .egg-info and __pycache__ directories are ignored by reload watcher
####

# Polling mode for watchfiles — needed on macOS Docker Desktop (virtiofs)
# Set WATCHFILES_FORCE_POLLING=false in .env if you use Linux or native inotify
export WATCHFILES_FORCE_POLLING="${WATCHFILES_FORCE_POLLING:-true}"

# Build reload paths — only watch plugins_dev to reduce CPU overhead
RELOAD_ARGS=""
IGNORE_ARGS=""
if [ -d /opt/netbox/plugins_dev ]; then
    RELOAD_ARGS="--reload-paths /opt/netbox/plugins_dev/"
    # Ignore all .egg-info directories created by editable installs
    for egg_dir in /opt/netbox/plugins_dev/*/*.egg-info; do
        if [ -d "$egg_dir" ]; then
            IGNORE_ARGS="${IGNORE_ARGS} --reload-ignore-paths ${egg_dir}"
        fi
    done
fi

# Optionally watch NetBox core (set WATCH_NETBOX_CORE=true to enable)
if [ "${WATCH_NETBOX_CORE:-false}" = "true" ]; then
    RELOAD_ARGS="${RELOAD_ARGS} --reload-paths /opt/netbox/netbox/"
fi

# ── Warm-up: send a request after Granian starts to pre-load Django ──
# Runs in background, waits for the port, then hits /login/ to trigger
# the WSGI app initialization so the first real user request is fast.
(
    sleep 3
    for i in $(seq 1 20); do
        if curl -sf -o /dev/null http://localhost:8080/login/ 2>/dev/null; then
            echo "🔥 Warm-up request completed — WSGI app is ready"
            break
        fi
        sleep 1
    done
) &

exec granian \
  --host "::" \
  --port "8080" \
  --interface "wsgi" \
  --no-ws \
  --workers "${GRANIAN_WORKERS:-1}" \
  --respawn-failed-workers \
  --backpressure "${GRANIAN_BACKPRESSURE:-${GRANIAN_WORKERS:-1}}" \
  --loop "uvloop" \
  --blocking-threads "${GRANIAN_BLOCKING_THREADS:-2}" \
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
  ${IGNORE_ARGS} \
  --reload-tick "${GRANIAN_RELOAD_TICK:-2000}" \
  --reload-ignore-dirs "__pycache__" \
  --reload-ignore-patterns ".*\\.pyc$" \
  "netbox.granian:application"
