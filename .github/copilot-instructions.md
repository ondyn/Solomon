# Solomon - GitHub Copilot Instructions

## Project Overview

Solomon is a **facility management system** for managing apartment buildings under SVJ (Společenství vlastníků jednotek - Association of Unit Owners) in the Czech Republic. It manages buildings, flats, owners, tenants, and provides a full audit trail of all changes.

## Reference-Only Directories

- **`./netbox/`** and **`./netbox-docker/`** are reference directories only - used for understanding NetBox internals, API definitions, and containerization examples.
- **Never import, reference, or include files from `./netbox/` or `./netbox-docker/` in Solomon application code, Docker configs, or any project files.**
- Solomon's own Docker/configuration files live at the project root (e.g., `docker-compose.yml`, `docker/`).

## Terminal Safety Rules

- **Never use heredoc syntax** (`<<EOF`, `<<'EOF'`, `cat <<EOF`) in terminal commands - they cause terminal disconnects
- **Never use `python3 -c "long code"`** or `python -c "..."` with multi-line code in terminal - use a temporary script file instead
- When you need to run multi-line Python: create a `.py` file, run it, then delete it
- Keep terminal commands short and single-line; chain with `&&` if needed

## Code Style Rules

- **Never use em dashes (`—`) anywhere in code** - use a plain hyphen (`-`) instead, in comments, docstrings, strings, and templates

## Localization

- **Every feature change, addition, or new plugin must include localization** - English (default) and Czech at minimum.
- All user-facing strings must be wrapped with Django's translation functions: `_()` for Python, `{% trans %}` / `{% blocktrans %}` in templates.
- Czech translations live in `locale/cs/LC_MESSAGES/django.po` inside each plugin. After adding strings, run `makemessages` then update the `.po` file, and compile with `compilemessages`.
- Commands (inside container):
  - Extract strings: `docker compose exec netbox python manage.py makemessages -l cs --ignore=netbox`
  - Compile: `docker compose exec netbox python manage.py compilemessages`
- Never leave new UI strings untranslated.

## Testing

- **Reuse the test database where possible** - restoring from a dump is slow; only do it when the schema changed, fixtures changed, or the test explicitly requires a clean slate.
- When iterating on logic or templates, run tests against the existing database and only restore when truly necessary.
- To restore: `./restore_db.sh backup/local/<snapshot>` (or the appropriate backup path).

## Debugging and Logs

- **App runs in Docker** - To debug or view logs, you must use Docker Compose:
  - View logs: `docker compose logs netbox` (or add `-f` for follow mode)
  - View specific number of logs: `docker compose logs -n 50 netbox`
  - See only recent logs: `docker compose logs --tail=100 netbox`
  - Execute commands in container: `docker compose exec netbox python manage.py <command>`
  - Rebuild and restart: `docker compose down && docker compose build --no-cache netbox && docker compose up -d netbox`
