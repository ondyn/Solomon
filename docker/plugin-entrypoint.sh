#!/bin/bash
####
## Solomon - Plugin Entrypoint
##
## Runs before the main NetBox entrypoint.
## Installs local (editable) plugins from /opt/netbox/plugins_dev/
## so that code changes are reflected immediately.
## Also runs collectstatic to pick up plugin static files.
##
## Note: This script may need write access to site-packages for editable installs.
## The container group is root (gid 0) which has write permission.
####

set -e

INSTALLED_PLUGIN=false

# Install each local plugin in editable mode (skip if already installed)
if [ -d /opt/netbox/plugins_dev ]; then
    for plugin_dir in /opt/netbox/plugins_dev/*/; do
        if [ -f "${plugin_dir}pyproject.toml" ] || [ -f "${plugin_dir}setup.py" ] || [ -f "${plugin_dir}setup.cfg" ]; then
            # Extract package name from directory (e.g. solomon_theme → solomon-theme)
            pkg_name=$(basename "${plugin_dir}" | tr '_' '-')
            # Check if already installed as editable from this path
            if /opt/netbox/venv/bin/python -c \
                "from importlib.metadata import distribution; d = distribution('${pkg_name}'); exit(0 if 'plugins_dev' in str(d._path) else 1)" \
                2>/dev/null; then
                echo "📦 Plugin already installed: ${plugin_dir}"
            else
                echo "📦 Installing local plugin: ${plugin_dir}"
                /usr/local/bin/uv pip install --python /opt/netbox/venv/bin/python \
                    -e "${plugin_dir}" --no-deps 2>&1 | tail -3
                INSTALLED_PLUGIN=true
            fi
        fi
    done
fi

# Collect static files from plugins (only if we installed something)
if [ "$INSTALLED_PLUGIN" = true ]; then
    echo "📦 Collecting static files from plugins..."
    /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py collectstatic --no-input 2>&1 | tail -5
fi

# Replace NetBox logos/favicon with Solomon branding at the static root level.
# This ensures the browser fetches Solomon logos directly — no JS interception needed.
STATIC_ROOT="/opt/netbox/netbox/static"
THEME_IMG="/opt/netbox/netbox/static/solomon_theme/img"
if [ -d "$THEME_IMG" ]; then
    for logo_file in logo_netbox_bright_teal.svg logo_netbox_dark_teal.svg; do
        if [ -f "${THEME_IMG}/${logo_file}" ]; then
            cp -f "${THEME_IMG}/${logo_file}" "${STATIC_ROOT}/${logo_file}"
        fi
    done
    # Replace favicon (netbox.ico) with Solomon SVG favicon
    if [ -f "${THEME_IMG}/favicon.svg" ]; then
        cp -f "${THEME_IMG}/favicon.svg" "${STATIC_ROOT}/netbox.ico"
    fi
    echo "🎨 Solomon branding applied to static root"
fi

# Hand off to the original NetBox entrypoint + our dev launch script
exec /opt/netbox/docker-entrypoint.sh "$@"
