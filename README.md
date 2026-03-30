# Solomon — Facility Management System

Facility management system for BD Salounova — managing apartment buildings under SVJ in the Czech Republic.

- **Repository:** [ondyn/Solomon](https://github.com/ondyn/Solomon)
- **Website:** [bdsalounova.cz](https://www.bdsalounova.cz/)
- **Design Document:** [DESIGN.md](DESIGN.md) — full system architecture, data model, and requirements

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 5.x (Python 3.12+) |
| **Frontend** | Django Templates + HTMX + Bootstrap 5 |
| **Database** | PostgreSQL 16 (SQLite for local dev) |
| **Package Manager** | [uv](https://docs.astral.sh/uv/) (fast Python package manager by Astral) |
| **Linting & Formatting** | Ruff |
| **Type Checking** | mypy + django-stubs |
| **Testing** | pytest + pytest-django + factory-boy |
| **Containerization** | Docker + Docker Compose |

---

## Prerequisites

- **Python 3.12+** — [python.org](https://www.python.org/downloads/)
- **uv** — fast Python package manager (installed automatically by `make install`, or manually):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Docker & Docker Compose** — only if using the Docker workflow
- **make** — pre-installed on macOS/Linux (optional but recommended)

---

## Quick Start (Local — without Docker)

```bash
# 1. Clone the repository
git clone https://github.com/ondyn/Solomon.git
cd Solomon

# 2. Full setup (installs uv, syncs dependencies, creates .env, runs migrations)
make init

# 3. Create admin account
make createsuperuser

# 4. Start development server
make run
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Step-by-step (without make)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv and install all dependencies (including dev)
uv sync

# Create environment file
cp .env.example .env            # Edit as needed

# Run database migrations
uv run python manage.py migrate

# Create admin user
uv run python manage.py createsuperuser

# Start development server
uv run python manage.py runserver
```

---

## Quick Start (Docker)

```bash
# 1. Full Docker setup (build, start PostgreSQL + Django, run migrations)
make docker-init

# 2. Create admin account
make docker-createsuperuser
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Step-by-step (without make)

```bash
# Build and start services (PostgreSQL + Django)
docker compose up -d

# Run migrations
docker compose exec web uv run python manage.py migrate

# Create admin user
docker compose exec web uv run python manage.py createsuperuser
```

---

## Development

### Common Commands

All commands are available via `make`. Run `make help` to see the full list.

| Command | Description |
|---------|-------------|
| `make run` | Start Django dev server on `localhost:8000` |
| `make run-debug` | Start Django with debugpy on port 5678 |
| `make migrate` | Run database migrations |
| `make makemigrations` | Create new migrations |
| `make createsuperuser` | Create Django superuser |
| `make shell` | Open Django interactive shell (IPython) |
| `make collectstatic` | Collect static files |

### Direct uv Commands

If you prefer not to use `make`:

```bash
uv run python manage.py runserver           # Start dev server
uv run python manage.py migrate             # Run migrations
uv run python manage.py makemigrations      # Create migrations
uv run python manage.py createsuperuser     # Create admin user
uv run python manage.py shell               # Django shell
```

### Adding Dependencies

```bash
uv add <package>                            # Add a runtime dependency
uv add --group dev <package>                # Add a dev-only dependency
uv sync                                     # Re-sync after editing pyproject.toml manually
```

### Debugging

**Local (VS Code):**
```bash
make run-debug                              # Starts debugpy listener on port 5678
```
Then attach VS Code debugger to `localhost:5678`.

**Docker:**
```bash
docker compose -f docker-compose.yml -f docker-compose.debug.yml up
```
Attach VS Code to `localhost:5678`. Port mapping is in `docker-compose.yml`.

**Django Debug Toolbar** is auto-enabled in dev settings (`solomon/settings/dev.py`).

---

## Code Quality

| Command | Description |
|---------|-------------|
| `make lint` | Run Ruff linter (with auto-fix) |
| `make format` | Run Ruff formatter |
| `make typecheck` | Run mypy type checker |
| `make check` | Run all three: lint + format + typecheck |
| `make pre-commit` | Run all pre-commit hooks |

### Pre-commit Hooks (one-time setup)

```bash
make pre-commit-install                     # Install git hooks
# Now hooks run automatically on every git commit
```

### Manual quality checks

```bash
uv run ruff check --fix .                   # Lint with auto-fix
uv run ruff format .                        # Format code
uv run mypy .                               # Type checking
uv run pre-commit run --all-files           # All pre-commit hooks
```

---

## Testing

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make test-cov` | Run tests with coverage report |
| `make test-fast` | Run tests excluding `@pytest.mark.slow` |
| `make test-verbose` | Run tests with verbose output |

### Direct commands

```bash
uv run pytest                               # Run all tests
uv run pytest --cov --cov-report=term-missing  # With coverage
uv run pytest -m "not slow"                 # Skip slow tests
uv run pytest buildings/                    # Run tests for one app
uv run pytest -k "test_building_create"     # Run specific test
```

Test settings are in `solomon/settings/test.py` (in-memory SQLite, fast password hasher). Coverage threshold is **70%** (configured in `pyproject.toml`).

---

## Docker Commands

| Command | Description |
|---------|-------------|
| `make docker-build` | Build development images |
| `make docker-up` | Start services |
| `make docker-down` | Stop services |
| `make docker-restart` | Restart services |
| `make docker-logs` | Tail container logs |
| `make docker-migrate` | Run migrations in container |
| `make docker-createsuperuser` | Create admin in container |
| `make docker-shell` | Django shell in container |
| `make docker-bash` | Bash shell in container |
| `make docker-rebuild` | Full rebuild from scratch (no cache) |
| `make docker-init` | Complete setup: build + start + migrate |

---

## Production

### Build Production Image

```bash
# Build the production Docker image (uses multi-stage build with uv)
make prod-build

# Or directly:
docker compose -f docker-compose.yml build --target production
```

The production image:
- Uses `uv sync --frozen --no-dev` (only production dependencies)
- Runs with **gunicorn** (3 workers)
- Collects static files automatically via **whitenoise**
- No dev tools, no debugpy, no debug toolbar

### Production Environment Variables

Create a `.env` file (see `.env.example`) with production values:

```bash
DJANGO_SECRET_KEY=<strong-random-string>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.cz,www.yourdomain.cz
DJANGO_SETTINGS_MODULE=solomon.settings.prod
DATABASE_URL=postgres://user:password@host:5432/solomon
SECURE_SSL_REDIRECT=True
```

### Run Production

```bash
# Start with production target
make prod-up

# Run migrations
docker compose exec web python manage.py migrate

# Create initial admin
docker compose exec web python manage.py createsuperuser

# Collect static (done automatically in Dockerfile, but can re-run)
docker compose exec web python manage.py collectstatic --noinput
```

### Production Checklist

- [ ] Set `DJANGO_SECRET_KEY` to a strong random value
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Set `DJANGO_ALLOWED_HOSTS` to your domain(s)
- [ ] Set `DATABASE_URL` to your PostgreSQL connection string
- [ ] Set `SECURE_SSL_REDIRECT=True`
- [ ] Configure email backend (SMTP) for notifications
- [ ] Run `python manage.py check --deploy` to verify settings

---

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
