#!/bin/bash
####
## Solomon - Plugin Entrypoint
##
## Runs before the main NetBox entrypoint.
## Installs local (editable) plugins from /opt/netbox/plugins_dev/
## so that code changes are reflected immediately.
##
## Note: This script may need write access to site-packages for editable installs.
## The container group is root (gid 0) which has write permission.
####

set -e

# Install each local plugin in editable mode
if [ -d /opt/netbox/plugins_dev ]; then
    for plugin_dir in /opt/netbox/plugins_dev/*/; do
        if [ -f "${plugin_dir}setup.py" ] || [ -f "${plugin_dir}setup.cfg" ] || [ -f "${plugin_dir}pyproject.toml" ]; then
            echo "📦 Installing local plugin: ${plugin_dir}"
            /usr/local/bin/uv pip install --python /opt/netbox/venv/bin/python \
                -e "${plugin_dir}" --no-deps 2>&1 | tail -3
        fi
    done
fi

# Hand off to the original NetBox entrypoint + our dev launch script
exec /opt/netbox/docker-entrypoint.sh "$@"
