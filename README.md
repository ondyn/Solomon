# Solomon — Facility Management System# Solomon — Facility Management System



Facility management system for BD Salounova — managing apartment buildings under SVJ in the Czech Republic.Facility management system for BD Salounova — managing apartment buildings under SVJ in the Czech Republic.



- **Repository:** [ondyn/Solomon](https://github.com/ondyn/Solomon)- **Repository:** [ondyn/Solomon](https://github.com/ondyn/Solomon)

- **Website:** [bdsalounova.cz](https://www.bdsalounova.cz/)- **Website:** [bdsalounova.cz](https://www.bdsalounova.cz/)

- **Design Document:** [DESIGN.md](DESIGN.md) — full system architecture, data model, and requirements- **Design Document:** [DESIGN.md](DESIGN.md) — full system architecture, data model, and requirements



------



## Tech Stack## Tech Stack



| Layer | Technology || Layer | Technology |

|-------|-----------||-------|-----------|

| **Backend** | Django 5.x (Python 3.12+) || **Backend** | Django 5.x (Python 3.12+) |

| **Frontend** | Django Templates + HTMX + Bootstrap 5 || **Frontend** | Django Templates + HTMX + Bootstrap 5 |

| **Database** | PostgreSQL 16 || **Database** | PostgreSQL 16 (SQLite for local dev) |

| **Package Manager** | [uv](https://docs.astral.sh/uv/) (fast Python package manager by Astral) || **Package Manager** | [uv](https://docs.astral.sh/uv/) (fast Python package manager by Astral) |

| **Linting & Formatting** | Ruff || **Linting & Formatting** | Ruff |

| **Type Checking** | mypy + django-stubs || **Type Checking** | mypy + django-stubs |

| **Testing** | pytest + pytest-django + factory-boy || **Testing** | pytest + pytest-django + factory-boy |

| **Containerization** | Docker + Docker Compose || **Containerization** | Docker + Docker Compose |



------



## Prerequisites## Prerequisites



- **Docker & Docker Compose** — [docker.com](https://docs.docker.com/get-docker/)- **Python 3.12+** — [python.org](https://www.python.org/downloads/)

- **make** — pre-installed on macOS/Linux- **uv** — fast Python package manager (installed automatically by `make install`, or manually):

  ```bash

That's it! Everything else (Python, uv, dependencies) lives inside the Docker container.  curl -LsSf https://astral.sh/uv/install.sh | sh

  ```

---- **Docker & Docker Compose** — only if using the Docker workflow

- **make** — pre-installed on macOS/Linux (optional but recommended)

## Quick Start

---

```bash

# 1. Clone the repository## Quick Start (Local — without Docker)

git clone https://github.com/ondyn/Solomon.git

cd Solomon```bash

# 1. Clone the repository

# 2. Full setup (builds images, starts PostgreSQL + Django, runs migrations)git clone https://github.com/ondyn/Solomon.git

make initcd Solomon



# 3. Create admin account# 2. Full setup (installs uv, syncs dependencies, creates .env, runs migrations)

make createsuperusermake init



# 4. Open the app# 3. Create admin account

open http://localhost:8000make createsuperuser

```

# 4. Start development server

**Live reload** is built-in — edit any `.py` file and Django restarts automatically inside the container. No rebuild needed.make run

```

### Step-by-step (without make)

Open [http://localhost:8000](http://localhost:8000) in your browser.

```bash

docker compose build### Step-by-step (without make)

docker compose up -d

docker compose exec web uv run python manage.py migrate```bash

docker compose exec web uv run python manage.py createsuperuser# Install uv

```curl -LsSf https://astral.sh/uv/install.sh | sh



---# Create venv and install all dependencies (including dev)

uv sync

## Development

# Create environment file

### Common Commandscp .env.example .env            # Edit as needed



All commands run inside Docker. Use `make help` to see the full list.# Run database migrations

uv run python manage.py migrate

| Command | Description |

|---------|-------------|# Create admin user

| `make up` | Start services (Django + PostgreSQL) |uv run python manage.py createsuperuser

| `make down` | Stop services |

| `make restart` | Restart services |# Start development server

| `make logs` | Tail container logs |uv run python manage.py runserver

| `make migrate` | Run database migrations |```

| `make makemigrations` | Create new migrations |

| `make createsuperuser` | Create Django superuser |---

| `make shell` | Open Django interactive shell |

| `make bash` | Open bash in the web container |## Quick Start (Docker)

| `make collectstatic` | Collect static files |

```bash

### How Live Reload Works# 1. Full Docker setup (build, start PostgreSQL + Django, run migrations)

make docker-init

Your source code is **bind-mounted** into the container (`volumes: .:/app`). When you save a file:

# 2. Create admin account

1. The change is immediately visible inside the containermake docker-createsuperuser

2. Django's `runserver` detects the `.py` change and auto-restarts```

3. Refresh your browser — done!

Open [http://localhost:8000](http://localhost:8000) in your browser.

No need to rebuild or restart the container for code changes. You only need `make rebuild` when changing `pyproject.toml` or `Dockerfile`.

### Step-by-step (without make)

### Adding Dependencies

```bash

```bash# Build and start services (PostgreSQL + Django)

# Add a runtime dependencydocker compose up -d

docker compose exec web uv add <package>

# Run migrations

# Add a dev-only dependencydocker compose exec web uv run python manage.py migrate

docker compose exec web uv add --group dev <package>

# Create admin user

# After manual edits to pyproject.toml, rebuilddocker compose exec web uv run python manage.py createsuperuser

make rebuild```

```

---

---

## Development

## Debugging

### Common Commands

### VS Code + Docker (recommended)

All commands are available via `make`. Run `make help` to see the full list.

1. **Start debug server:**

   ```bash| Command | Description |

   make debug|---------|-------------|

   ```| `make run` | Start Django dev server on `localhost:8000` |

   This launches Django with `debugpy` listening on port **5678** and waits for VS Code to attach.| `make run-debug` | Start Django with debugpy on port 5678 |

| `make migrate` | Run database migrations |

2. **Attach VS Code:**| `make makemigrations` | Create new migrations |

   - Select **"Django: Docker Attach"** in the Run & Debug panel| `make createsuperuser` | Create Django superuser |

   - Press **F5**| `make shell` | Open Django interactive shell (IPython) |

| `make collectstatic` | Collect static files |

3. **Set breakpoints** in any `.py` file — they work because path mappings are configured in `.vscode/launch.json`.

### Direct uv Commands

### Django Debug Toolbar

If you prefer not to use `make`:

Auto-enabled in dev settings (`solomon/settings/dev.py`). Visible on `localhost:8000` for any HTML response.

```bash

---uv run python manage.py runserver           # Start dev server

uv run python manage.py migrate             # Run migrations

## Database Backup & Restoreuv run python manage.py makemigrations      # Create migrations

uv run python manage.py createsuperuser     # Create admin user

| Command | Description |uv run python manage.py shell               # Django shell

|---------|-------------|```

| `make db-backup` | Backup to `backups/solomon_<timestamp>.sql.gz` |

| `make db-restore FILE=backups/xxx.sql.gz` | Restore from a backup file |### Adding Dependencies

| `make db-reset` | Drop & recreate DB, then run migrations (empty DB) |

| `make db-psql` | Open interactive psql shell |```bash

uv add <package>                            # Add a runtime dependency

### Examplesuv add --group dev <package>                # Add a dev-only dependency

uv sync                                     # Re-sync after editing pyproject.toml manually

```bash```

# Create a backup before risky changes

make db-backup### Debugging



# Restore a specific backup**Local (VS Code):**

make db-restore FILE=backups/solomon_20260330_143000.sql.gz```bash

make run-debug                              # Starts debugpy listener on port 5678

# Backup to a custom filename```

make db-backup BACKUP_FILE=backups/before-migration.sql.gzThen attach VS Code debugger to `localhost:5678`.



# Reset DB to clean state**Docker:**

make db-reset```bash

```docker compose -f docker-compose.yml -f docker-compose.debug.yml up

```

Backups are stored in the `backups/` directory (gitignored).Attach VS Code to `localhost:5678`. Port mapping is in `docker-compose.yml`.



---**Django Debug Toolbar** is auto-enabled in dev settings (`solomon/settings/dev.py`).



## Code Quality---



| Command | Description |## Code Quality

|---------|-------------|

| `make lint` | Run Ruff linter (with auto-fix) || Command | Description |

| `make format` | Run Ruff formatter ||---------|-------------|

| `make typecheck` | Run mypy type checker || `make lint` | Run Ruff linter (with auto-fix) |

| `make check` | Run all three: lint + format + typecheck || `make format` | Run Ruff formatter |

| `make pre-commit` | Run all pre-commit hooks || `make typecheck` | Run mypy type checker |

| `make check` | Run all three: lint + format + typecheck |

### Pre-commit Hooks (one-time setup)| `make pre-commit` | Run all pre-commit hooks |



```bash### Pre-commit Hooks (one-time setup)

make pre-commit-install

# Now hooks run automatically on every git commit```bash

```make pre-commit-install                     # Install git hooks

# Now hooks run automatically on every git commit

---```



## Testing### Manual quality checks



| Command | Description |```bash

|---------|-------------|uv run ruff check --fix .                   # Lint with auto-fix

| `make test` | Run all tests |uv run ruff format .                        # Format code

| `make test-cov` | Run tests with coverage report |uv run mypy .                               # Type checking

| `make test-fast` | Run tests excluding `@pytest.mark.slow` |uv run pre-commit run --all-files           # All pre-commit hooks

| `make test-verbose` | Run tests with verbose output |```



Test settings are in `solomon/settings/test.py` (in-memory SQLite, fast password hasher). Coverage threshold is **70%** (configured in `pyproject.toml`).---



---## Testing



## Production| Command | Description |

|---------|-------------|

### Build Production Image| `make test` | Run all tests |

| `make test-cov` | Run tests with coverage report |

```bash| `make test-fast` | Run tests excluding `@pytest.mark.slow` |

make prod-build| `make test-verbose` | Run tests with verbose output |

```

### Direct commands

The production image:

- Uses `uv sync --frozen --no-dev` (only production dependencies)```bash

- Runs with **gunicorn** (3 workers)uv run pytest                               # Run all tests

- Collects static files automatically via **whitenoise**uv run pytest --cov --cov-report=term-missing  # With coverage

- No dev tools, no debugpy, no debug toolbaruv run pytest -m "not slow"                 # Skip slow tests

uv run pytest buildings/                    # Run tests for one app

### Production Environment Variablesuv run pytest -k "test_building_create"     # Run specific test

```

Create a `.env` file (see `.env.example`) with production values:

Test settings are in `solomon/settings/test.py` (in-memory SQLite, fast password hasher). Coverage threshold is **70%** (configured in `pyproject.toml`).

```bash

DJANGO_SECRET_KEY=<strong-random-string>---

DJANGO_DEBUG=False

DJANGO_ALLOWED_HOSTS=yourdomain.cz,www.yourdomain.cz## Docker Commands

DJANGO_SETTINGS_MODULE=solomon.settings.prod

DATABASE_URL=postgres://user:password@host:5432/solomon| Command | Description |

SECURE_SSL_REDIRECT=True|---------|-------------|

```| `make docker-build` | Build development images |

| `make docker-up` | Start services |

### Production Checklist| `make docker-down` | Stop services |

| `make docker-restart` | Restart services |

- [ ] Set `DJANGO_SECRET_KEY` to a strong random value| `make docker-logs` | Tail container logs |

- [ ] Set `DJANGO_DEBUG=False`| `make docker-migrate` | Run migrations in container |

- [ ] Set `DJANGO_ALLOWED_HOSTS` to your domain(s)| `make docker-createsuperuser` | Create admin in container |

- [ ] Set `DATABASE_URL` to your PostgreSQL connection string| `make docker-shell` | Django shell in container |

- [ ] Set `SECURE_SSL_REDIRECT=True`| `make docker-bash` | Bash shell in container |

- [ ] Configure email backend (SMTP) for notifications| `make docker-rebuild` | Full rebuild from scratch (no cache) |

- [ ] Run `python manage.py check --deploy` to verify settings| `make docker-init` | Complete setup: build + start + migrate |



------



## Localization## Production



The primary language is Czech (`cs`), English (`en`) is secondary.### Build Production Image



```bash```bash

make messages          # Generate/update .po translation files# Build the production Docker image (uses multi-stage build with uv)

make compilemessages   # Compile .po to .mo filesmake prod-build

```

# Or directly:

---docker compose -f docker-compose.yml build --target production

```

## Project Structure

The production image:

```- Uses `uv sync --frozen --no-dev` (only production dependencies)

FM-Salounova/                    # Git repository root- Runs with **gunicorn** (3 workers)

├── manage.py                    # Django management command- Collects static files automatically via **whitenoise**

├── pyproject.toml               # Project metadata, dependencies, tool config- No dev tools, no debugpy, no debug toolbar

├── uv.lock                     # Locked dependency versions

├── Makefile                    # Development task runner (Docker-first)### Production Environment Variables

├── Dockerfile                  # Multi-stage build (builder / production / development)

├── docker-compose.yml          # Dev: PostgreSQL + Django with live reloadCreate a `.env` file (see `.env.example`) with production values:

├── .env.example                # Environment variables template

├── .pre-commit-config.yaml     # Pre-commit hooks config```bash

├── conftest.py                 # Shared pytest fixturesDJANGO_SECRET_KEY=<strong-random-string>

├── DESIGN.md                   # Full software design documentDJANGO_DEBUG=False

│DJANGO_ALLOWED_HOSTS=yourdomain.cz,www.yourdomain.cz

├── solomon/                    # Django project packageDJANGO_SETTINGS_MODULE=solomon.settings.prod

│   ├── settings/               # base.py / dev.py / prod.py / test.pyDATABASE_URL=postgres://user:password@host:5432/solomon

│   ├── urls.py                 # Root URL configurationSECURE_SSL_REDIRECT=True

│   └── context_processors.py   # App version context processor```

│

├── core/                       # Shared: base models, permissions, CUZK integration### Run Production

├── buildings/                  # Building management module

├── flats/                      # Flat management module```bash

├── owners/                     # Owner management module (includes FlatOwner)# Start with production target

├── tenants/                    # Tenant management modulemake prod-up

├── accounts/                   # User authentication

│# Run migrations

├── templates/                  # Django templates (base.html, app templates)docker compose exec web python manage.py migrate

├── static/                     # Static files (CSS, JS, images)

├── locale/                     # Translation files (cs, en)# Create initial admin

└── backups/                    # Database backups (gitignored)docker compose exec web python manage.py createsuperuser

```

# Collect static (done automatically in Dockerfile, but can re-run)

---docker compose exec web python manage.py collectstatic --noinput

```

## Cleanup

### Production Checklist

```bash

make clean                      # Remove __pycache__, .mypy_cache, etc.- [ ] Set `DJANGO_SECRET_KEY` to a strong random value

make clean-all                  # Stop Docker, remove volumes, clean everything- [ ] Set `DJANGO_DEBUG=False`

```- [ ] Set `DJANGO_ALLOWED_HOSTS` to your domain(s)

- [ ] Set `DATABASE_URL` to your PostgreSQL connection string

---- [ ] Set `SECURE_SSL_REDIRECT=True`

- [ ] Configure email backend (SMTP) for notifications

## License- [ ] Run `python manage.py check --deploy` to verify settings



MIT---


## Localization

The primary language is Czech (`cs`), English (`en`) is secondary.

```bash
make messages                               # Generate/update .po translation files
make compilemessages                        # Compile .po to .mo files
```

Or directly:
```bash
uv run django-admin makemessages -l cs
uv run django-admin compilemessages
```

---

## Project Structure

```
FM-Salounova/                    # Git repository root
├── manage.py                    # Django management command
├── pyproject.toml               # Project metadata, dependencies, tool config
├── uv.lock                     # Locked dependency versions
├── Makefile                    # Development task runner
├── Dockerfile                  # Multi-stage build (builder / production / development)
├── docker-compose.yml          # Dev: PostgreSQL + Django
├── docker-compose.debug.yml    # Debug override (debugpy on port 5678)
├── .env.example                # Environment variables template
├── .pre-commit-config.yaml     # Pre-commit hooks config
├── conftest.py                 # Shared pytest fixtures
├── DESIGN.md                   # Full software design document
│
├── solomon/                    # Django project package
│   ├── settings/               # base.py / dev.py / prod.py / test.py
│   ├── urls.py                 # Root URL configuration
│   └── context_processors.py   # App version context processor
│
├── core/                       # Shared: base models, permissions, CUZK integration
├── buildings/                  # Building management module
├── flats/                      # Flat management module
├── owners/                     # Owner management module (includes FlatOwner)
├── tenants/                    # Tenant management module
├── accounts/                   # User authentication
│
├── templates/                  # Django templates (base.html, app templates)
├── static/                     # Static files (CSS, JS, images)
└── locale/                     # Translation files (cs, en)
```

---

## Cleanup

```bash
make clean                                  # Remove __pycache__, .mypy_cache, etc.
make clean-all                              # Also remove .venv and db.sqlite3
```

---

## License

MIT
