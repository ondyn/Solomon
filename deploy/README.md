# Google Cloud deployment

## Architecture and cost model

Solomon runs on one `e2-medium` Compute Engine VM:

- Caddy for HTTPS
- NetBox web with one Granian worker
- NetBox RQ worker
- PostgreSQL 16
- Two Valkey services for tasks and cache
- Docker volumes on a 30 GB standard persistent disk

Artifact Registry stores production images and private Python wheels. Secret
Manager stores database, Django, and Valkey credentials. Backups are initiated
manually from the administrator's Mac and downloaded to `backup/cloud/`.

This is the lowest-cost practical GCP topology for a few occasional users. There
is no continuously billed Cloud SQL, Memorystore, or GKE cluster. When the VM is
stopped, vCPU and memory billing stops. Its persistent disk and stored Artifact
Registry data continue to incur small charges. Deleting the runtime also removes
the disk; that is safe only after a verified Mac backup.

## 1. Mac prerequisites

1. Create a Google Cloud project with billing enabled.
2. Install the Google Cloud CLI and run `gcloud auth login` and
   `gcloud auth application-default login`.
3. Copy `deploy/production.env.example` to `deploy/production.env`.
4. Set `DOMAIN`, `ACME_EMAIL`, and `ALLOWED_HOSTS` in that file.
   - **Custom domain** (e.g. `solo-mon.site`): point the domain's `A` record
     to the VM's external IP, then run `sh deploy/set-custom-domain.sh`.
   - **No custom domain**: run `sh deploy/set-ip-domain.sh` after provisioning
     to derive a free `sslip.io` hostname and populate those values automatically.
5. Add the common settings to the root `.env` file once:

```dotenv
PROJECT_ID=solomon-504115
REGION=europe-west3
ZONE=europe-west3-a
VM_NAME=solomon
```

Mac-side deployment scripts load these values automatically through
`deploy/load-env.sh`. Explicitly exported values take precedence, so a one-off
command can still target another project or VM. The loader reads only
deployment-related keys and does not evaluate the root `.env` as shell code.

The root `.env`, `deploy/production.env`, and downloaded backups are ignored by
Git.

## 2. Provision the budget runtime

```sh
sh deploy/provision-gcp.sh
```

The script enables the required APIs and creates:

- Docker and Python Artifact Registry repositories
- Four credentials in Secret Manager
- A least-privilege VM service account
- One `e2-medium` VM with a 30 GB standard persistent disk

The script does not create Cloud SQL or Cloud Storage. If the VM already exists
with another machine type, stop it and rerun provisioning to resize it.

The VM uses an ephemeral external IP to avoid reserving an unused static IPv4
address. The IP can change after every stop/start cycle. To update Google Cloud
DNS automatically, provide its managed-zone name and the application domain:

```sh
export DNS_ZONE=example-cz
export DOMAIN=solomon.example.cz
```

For DNS hosted elsewhere, `start.sh` prints the current address; update the
domain's `A` record manually. Caddy keeps its certificate data on the persistent
disk and renews certificates while the VM is running.

## 3. First release and updates

Set `NETBOX_VERSION` to an existing `netboxcommunity/netbox` image tag:

```sh
export NETBOX_VERSION=v4.5.8
sh deploy/release.sh
```

The release starts the VM when needed, then:

1. Runs Ruff lint and formatting checks
2. Builds the production image and runs Django plugin tests
3. Builds and publishes private plugin wheels
4. Builds and pushes a Git-tagged image with Cloud Build
5. Pulls the image, runs migrations, and checks container health

Create a Mac backup before a schema-changing release. Release does not silently
create or delete backups.

## 4. Weekly start/stop workflow

Start the VM and display or update its address:

```sh
sh deploy/start.sh
sh deploy/status.sh
```

After use, create a local backup and stop compute billing:

```sh
sh deploy/stop.sh --backup
```

To stop without making a backup:

```sh
sh deploy/stop.sh
```

Docker stops cleanly with the VM. Services with `restart: unless-stopped` start
again when Docker starts at the next VM boot. Expect up to two minutes before
NetBox becomes healthy.

## 5. Manual backups from the Mac

The VM must be running. Run:

```sh
sh deploy/backup-from-mac.sh
```

The script asks PostgreSQL for a consistent custom-format dump, archives media,
reports, and scripts, downloads both to:

```text
backup/cloud/YYYYMMDD_HHMMSS/
```

It writes SHA-256 checksums and removes the temporary VM copy only after the
download is verified. Keep a second copy on another physical disk or independent
object-storage provider. A backup stored only on the same Mac is not sufficient
protection against loss or theft.

Restore a downloaded backup:

```sh
CONFIRM_REMOTE_RESTORE=solomon \
   sh deploy/restore-from-mac.sh backup/cloud/20260731_120000
```

Restore verifies checksums, starts the VM, uploads the backup, stops NetBox,
recreates PostgreSQL, replaces persistent application files, and restarts NetBox.
It is destructive. Test a restore before relying on this process.

## 6. Maximum savings while unused

### Stop the VM

Use this for normal weekly operation:

```sh
sh deploy/stop.sh --backup
```

This stops VM compute charges but retains the 30 GB disk, images, wheels, and
secrets. It provides the fastest restart and is the recommended balance.

### Delete the VM and disk

For a long inactive period, first make a backup, then explicitly confirm deletion:

```sh
sh deploy/backup-from-mac.sh
CONFIRM_DELETE=solomon sh deploy/destroy-runtime.sh backup/cloud/20260731_120000
```

This deletes the VM and its database/media disk. To also remove Artifact Registry
and Secret Manager storage:

```sh
CONFIRM_DELETE=solomon \
DELETE_ARTIFACT_REPOSITORIES=true \
DELETE_SECRETS=true \
sh deploy/destroy-runtime.sh backup/cloud/20260731_120000
```

Recreate and restore later:

```sh
sh deploy/provision-gcp.sh
export NETBOX_VERSION=v4.5.8
sh deploy/release.sh
sh deploy/restore-from-mac.sh backup/cloud/20260731_120000
```

Deleting Artifact Registry repositories means the next release must rebuild and
republish everything. IAM bindings and enabled APIs do not have an idle charge.

## 7. Private plugin packages

Increment each changed plugin's PEP 440 version in its `pyproject.toml`, then run:

```sh
sh deploy/publish-plugins.sh
```

Install a private wheel elsewhere with a short-lived token:

```sh
pip install --extra-index-url \
  "https://oauth2accesstoken:$(gcloud auth print-access-token)@europe-west3-python.pkg.dev/PROJECT_ID/solomon-python/simple/" \
  solomon-property==0.1.0
```

Never place a permanent access token in a requirements file or Docker layer.

## 8. Operations and rollback

From the Mac:

```sh
sh deploy/status.sh
gcloud compute ssh "$VM_NAME" --zone "$ZONE"
```

On the VM:

```sh
cd /opt/solomon
sh deploy/compose.sh --env-file .env.production -f docker-compose.production.yml ps
sh deploy/compose.sh --env-file .env.production -f docker-compose.production.yml logs --tail 100 netbox
```

Images are tagged by Git commit. To roll code back, set `SOLOMON_IMAGE` in the
VM's `.env.production` to an earlier tag and run Compose `up -d`. Do not roll back
across incompatible database migrations; restore the matching Mac backup.

Monitor VM disk utilization and external HTTPS availability. The manual-backup
process should also include a calendar reminder; there is intentionally no VM-side
timer because the VM is expected to spend most of its time stopped.

## 9. Operations runbook

Run the commands in this section from the repository root on the Mac. The common
settings are loaded from the root `.env` file:

```dotenv
PROJECT_ID=solomon-504115
REGION=europe-west3
ZONE=europe-west3-a
VM_NAME=solomon
```

Add `DNS_ZONE` and `DOMAIN` when the domain is managed by Google Cloud DNS.

### Run all remote migrations

Use the root-level shortcut:

```sh
./migrate_remote.sh
```

The script starts the VM if needed, downloads a full production backup, shows
the complete Django migration plan, applies all pending NetBox and plugin
migrations with `--no-input`, and displays the final container status. The
upstream NetBox startup also checks migrations, but this command provides an
explicit operational step after a database restore or before verifying a
release.

### First deployment

```sh
cp deploy/production.env.example deploy/production.env
# Edit deploy/production.env before continuing.

sh deploy/provision-gcp.sh

# If you have no custom domain, derive a free sslip.io hostname from the VM IP:
sh deploy/set-ip-domain.sh

export NETBOX_VERSION=v4.5.8
sh deploy/release.sh
sh deploy/status.sh
```

If DNS is hosted outside Google Cloud, use the address printed by `start.sh` or
`status.sh` to update the domain's `A` record. Re-run `set-ip-domain.sh` after
every stop/start cycle if you are using a `sslip.io` hostname, since the
ephemeral IP changes.

### First deployment with a custom domain

If you own a domain (e.g. `solo-mon.site`), set it up before running the first
release:

1. At your DNS registrar, update the `@` A record to the VM's external IP.
   Delete any AAAA records unless the VM has IPv6. Verify propagation:

   ```sh
   dig solo-mon.site A +short
   # should return the VM IP, e.g. 35.246.161.220
   ```

2. Run the setup script once DNS resolves correctly:

   ```sh
   export DOMAIN=solo-mon.site
   export ACME_EMAIL=admin@solo-mon.site
   sh deploy/set-custom-domain.sh
   ```

   The script updates `deploy/production.env`, patches `.env.production` on
   the VM, and restarts Caddy. Caddy obtains a Let's Encrypt certificate via
   HTTP-01 within 60 seconds.

3. Because the VM uses an ephemeral IP, re-run `set-custom-domain.sh` after
   every stop/start cycle to update the A record and Caddy configuration:

   ```sh
   sh deploy/start.sh
   # Update the A record at your registrar to the new IP printed by start.sh,
   # wait for propagation, then:
   export DOMAIN=solo-mon.site
   sh deploy/set-custom-domain.sh
   ```

### Normal weekly use

```sh
# Start compute and wait for VM bootstrap readiness.
sh deploy/start.sh
sh deploy/status.sh

# Use Solomon, then download a backup and stop compute billing.
sh deploy/stop.sh --backup
```

The backup must finish successfully before `stop.sh --backup` stops the VM.

### Safe application or plugin update

Increment the version in every changed plugin's `pyproject.toml`, then run:

```sh
sh deploy/start.sh
sh deploy/backup-from-mac.sh

export NETBOX_VERSION=v4.5.8
sh deploy/release.sh
sh deploy/status.sh

# Stop after verifying the updated application.
sh deploy/stop.sh
```

Keep the pre-update backup until the new version has been verified. If a release
contains incompatible migrations, restore that backup rather than only changing
the image tag.

### Manual backup without stopping

```sh
sh deploy/start.sh
sh deploy/backup-from-mac.sh
```

Confirm that the resulting directory contains `database.dump`, `files.tar.gz`,
`manifest.txt`, and `SHA256SUMS`.

### Restore after an application problem

```sh
sh deploy/restore-from-mac.sh backup/cloud/YYYYMMDD_HHMMSS
sh deploy/status.sh
```

Restore replaces the current database and persistent application files. Verify
that the selected backup timestamp is correct before running it.

### Restore only the database from a dump

From the project root on the administrator's Mac:

```sh
export PROJECT_ID=my-solomon-project
export ZONE=europe-west3-a
export VM_NAME=solomon

CONFIRM_REMOTE_RESTORE=solomon \
   ./restore_db_remote.sh backup/db_backup_20260807_125250.dump
```

This leaves production media, reports, and scripts unchanged. Before the
database is replaced, the script downloads a full production backup to
`backup/cloud/`. The confirmation value is mandatory because this operation
drops and recreates the production database.

### Recreate after deleting the runtime

```sh
sh deploy/provision-gcp.sh

export NETBOX_VERSION=v4.5.8
sh deploy/release.sh

sh deploy/restore-from-mac.sh backup/cloud/YYYYMMDD_HHMMSS
sh deploy/status.sh
```

### Long-term shutdown

For the normal low-cost option, retain the disk and stop only compute:

```sh
sh deploy/stop.sh --backup
```

For minimum idle cost, verify a local backup before deleting the VM and disk:

```sh
sh deploy/backup-from-mac.sh
CONFIRM_DELETE=solomon \
sh deploy/destroy-runtime.sh backup/cloud/YYYYMMDD_HHMMSS
```

Set `DELETE_ARTIFACT_REPOSITORIES=true` and `DELETE_SECRETS=true` only when their
contents should also be removed and a full rebuild on the next deployment is
acceptable.

### Script reference

| Script | Runs on | Purpose |
| --- | --- | --- |
| `provision-gcp.sh` | Mac | Creates or updates the VM, repositories, secrets, IAM, and enabled APIs |
| `set-ip-domain.sh` | Mac | Reads the VM's current external IP, sets a `sslip.io` DOMAIN in `production.env`, and restarts Caddy on the VM |
| `set-custom-domain.sh` | Mac | Updates `production.env` and the VM to use a custom domain, then restarts Caddy |
| `release.sh` | Mac | Runs checks, publishes plugins, builds the image, and updates the VM |
| `start.sh` | Mac | Starts the VM, waits for bootstrap, and reports or updates its IP address |
| `stop.sh` | Mac | Stops VM compute, optionally after a successful Mac backup |
| `status.sh` | Mac | Displays VM details and production container status |
| `backup-from-mac.sh` | Mac | Creates a VM backup, downloads it, verifies files, and removes the VM copy |
| `restore-from-mac.sh` | Mac | Verifies, uploads, and restores a selected local backup |
| `../restore_db_remote.sh` | Mac | Backs up production, then replaces only its database from a dump |
| `../migrate_remote.sh` | Mac | Shows and applies all remote NetBox and plugin migrations |
| `destroy-runtime.sh` | Mac | Deletes the VM and disk after explicit confirmation and backup validation |
| `check.sh` | Mac or CI | Runs formatting, linting, image build, and Django tests |
| `publish-plugins.sh` | Mac | Builds and uploads private Python wheels |
| `backup.sh` | VM/internal | Creates the PostgreSQL and persistent-file backup staging directory |
| `restore.sh` | VM/internal | Restores PostgreSQL and persistent files from a staged backup |
| `restore-database.sh` | VM/internal | Validates and restores PostgreSQL from a staged dump |
| `remote-update.sh` | VM/internal | Pulls a release image, starts services, and checks NetBox health |
| `compose.sh` | Mac or VM | Selects the available Docker Compose implementation |
| `load-env.sh` | Mac/internal | Loads allowlisted Google Cloud settings from root `.env` |