# How It Works
1) Local plugins in plugins are bind-mounted into the container at /opt/netbox/plugins_dev/
2) At container startup, plugin-entrypoint.sh runs uv pip install -e for each plugin — making them importable while keeping source on the host
3) Granian runs with --reload watching both NetBox core and plugins_dev/ — any .py file change triggers an immediate worker restart (~1 sec)
4) WATCHFILES_FORCE_POLLING=true ensures reliable change detection on macOS Docker Desktop (virtiofs doesn't forward inotify)
5) Third-party plugins go in plugin-requirements.txt and are baked into the image at build time
6) debugpy is activated by setting DEBUGPY_ENABLE=true in .env — VS Code attaches on port 5678

# key commands
```
docker compose build netbox      # Rebuild after changing plugin-requirements.txt
docker compose up -d             # Start (plugins auto-installed)
docker compose logs -f netbox    # Watch reload events
docker compose exec netbox python manage.py makemigrations <plugin>
docker compose exec netbox python manage.py migrate <plugin>
```
