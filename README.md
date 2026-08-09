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

# Local backup and restore

PostgreSQL and the persistent media, reports, and scripts volumes are backed up
together. This includes the source PDFs and SVG backgrounds uploaded by
`solomon_facilities`.

Backups are stored in `./backup/local` and use this format:

- `YYYYMMDD_HHMMSS/database.dump`
- `YYYYMMDD_HHMMSS/files.tar.gz`
- `YYYYMMDD_HHMMSS/SHA256SUMS`

Create a backup:

```sh
./backup_db.sh
```

Restore the latest full backup:

```sh
./restore_db.sh
```

Restore a specific timestamp:

```sh
./restore_db.sh 20260705_154210
```

Restore a specific dump file by relative or absolute path:

```sh
./restore_db.sh backup/db_backup_20260807_125250.dump
```

Legacy dump files restore only PostgreSQL and leave persistent files unchanged.

The database containers must be running before backup or restore commands are
executed. Run these commands from the project root. Restore replaces the entire
configured local database; create a fresh backup first if its current contents
may still be needed.

Restore behavior:

1) Validates the dump, file archive paths, and SHA-256 checksums
2) Stops local NetBox and its worker
3) Terminates active connections and drops the target DB
4) Creates a new empty DB
5) Replaces persistent files from the same backup
6) Starts NetBox and its worker again

If restore fails, the application services remain stopped so they cannot write
to a partially restored database.

# Remote Google Cloud full restore

Use `deploy/restore-from-mac.sh` to replace the production database and
persistent media, reports, and scripts from a full local backup directory:

```sh
export PROJECT_ID=my-solomon-project
export ZONE=europe-west3-a
export VM_NAME=solomon

CONFIRM_REMOTE_RESTORE=solomon \
	sh deploy/restore-from-mac.sh backup/local/20260809_195739
```

Create a separate full production backup with `deploy/backup-from-mac.sh` before
restoring local data. Deploy the application version containing all restored
plugin models and migrations before starting the restore.

# Remote Google Cloud migrations

Add the reusable Google Cloud settings to the root `.env` file once:

```dotenv
PROJECT_ID=solomon-504115
REGION=europe-west3
ZONE=europe-west3-a
VM_NAME=solomon
```

Mac-side scripts in `deploy/`, `restore_db_remote.sh`, and
`migrate_remote.sh` load these settings automatically. An explicitly exported
variable overrides the corresponding `.env` value for a one-off command.

Run all pending NetBox and plugin migrations:

```sh
./migrate_remote.sh
```

The migration shortcut starts the VM if necessary, downloads a full production
backup, displays the migration plan, runs `manage.py migrate --no-input` in the
production NetBox container, and prints the final production service status.

# Production deployment

See [deploy/README.md](deploy/README.md) for the Google Cloud architecture,
provisioning, releases, private plugin packages, and disaster recovery.
