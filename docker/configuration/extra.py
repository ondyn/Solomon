####
## Solomon - NetBox Extra Configuration
##
## This file is mounted into the NetBox container at /etc/netbox/config/extra.py
## Use it for settings that can't be set via environment variables.
## These settings override configuration.py values.
####

## Enable developer mode (allows makemigrations for plugins, etc.)
DEVELOPER = True

## ─── debugpy remote debugging ──────────────────────────────────────────────
## Start debugpy listener so VS Code can attach for breakpoint debugging.
## Set DEBUGPY_ENABLE=true in .env to activate.
import os
if os.environ.get("DEBUGPY_ENABLE", "false").lower() == "true":
    try:
        import debugpy
        debugpy_port = int(os.environ.get("DEBUGPY_PORT", "5678"))
        debugpy.listen(("0.0.0.0", debugpy_port))
        print(f"🐛 debugpy listening on 0.0.0.0:{debugpy_port}")
    except Exception as e:
        print(f"⚠️  debugpy failed to start: {e}")

## Uncomment to display a persistent banner
# BANNER_TOP = '<div class="text-center">Solomon Facility Management - NetBox</div>'

## Uncomment to set admin contacts
# ADMINS = [
#     ['Admin Name', 'admin@example.com'],
# ]

## Custom links, validators, etc. can go here

## ─── CUZK API key ──────────────────────────────────────────────────────────
## Read from environment variable CUZK_API_KEY.
## Set it in docker-compose.override.yml or a .env file.
CUZK_API_KEY = os.environ.get("CUZK_API_KEY", "")
