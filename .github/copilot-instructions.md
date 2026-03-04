# Solomon — GitHub Copilot Instructions

## Project Overview

Solomon is a **facility management system** for managing apartment buildings under SVJ (Společenství vlastníků jednotek — Association of Unit Owners) in the Czech Republic. It manages buildings, flats, owners, tenants, and provides a full audit trail of all changes.

- **Repository:** github.com/ondyn/Solomon
- **Design Document:** See `DESIGN.md` for full architecture, data model, and requirements.
- **Version:** Defined in `pyproject.toml` (`version = "0.1.0"`)

## Tech Stack

- **Backend:** Django 5.x (Python 3.12+)
- **Frontend:** Django Templates + HTMX + Bootstrap 5
- **Database:** PostgreSQL 16 (SQLite for local development without Docker)
- **Key packages:** django-environ, django-auditlog, django-safedelete, django-htmx, whitenoise
- **Linting & Formatting:** Ruff (replaces flake8, isort, black)
- **Type Checking:** mypy + django-stubs
- **Testing:** pytest + pytest-django + factory-boy + pytest-cov
- **Pre-commit:** pre-commit hooks for ruff, mypy, trailing whitespace, etc.
- **Localization:** Czech (cs) primary, English (en) secondary, via Django i18n
- **Dev Environment:** Docker Compose (PostgreSQL + Django) or local venv + SQLite
- **Deployment:** Docker, GitHub Actions CI/CD

## Project Structure

```
FM-Salounova/                # Git repository root
├── manage.py                # Django management command (defaults to settings.dev)
├── pyproject.toml           # Project metadata, ALL dependencies, ruff/mypy/pytest/coverage config
├── .env.example             # Template for environment variables
├── .gitignore
├── .pre-commit-config.yaml  # Pre-commit hooks (ruff, mypy, trailing-whitespace, etc.)
├── Dockerfile               # Multi-stage build (base → builder → development/production)
├── docker-compose.yml       # Local dev: PostgreSQL 16 + Django (ports 8000, 5678 for debugpy)
├── conftest.py              # Root-level shared pytest fixtures
├── DESIGN.md                # Full software design document
├── README.md                # Project readme
│
├── solomon/                 # Django project package
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py          # Shared settings (django-environ, apps, middleware, i18n, static)
│   │   ├── dev.py           # Development (DEBUG=True, debug_toolbar, console email)
│   │   ├── prod.py          # Production (DEBUG=False, HTTPS, HSTS, SMTP email)
│   │   └── test.py          # Testing (in-memory SQLite, fast password hasher, null logging)
│   ├── urls.py              # Root URL conf with i18n_patterns
│   ├── wsgi.py
│   ├── asgi.py
│   └── context_processors.py  # app_version context processor
│
├── core/                    # Shared app: base models, permissions, auth helpers
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # BaseModel (UUID pk, timestamps, SafeDeleteModel), @register_auditlog
│   ├── permissions.py       # Roles class (ADMIN, CHAIRMAN, BOARD_MEMBER, OWNER), MANAGEMENT_ROLES
│   └── admin.py
│
├── buildings/               # Building management module
│   ├── __init__.py, apps.py, models.py, views.py, forms.py, urls.py, admin.py
│
├── flats/                   # Flat management module
│   ├── __init__.py, apps.py, models.py, views.py, forms.py, urls.py, admin.py
│
├── owners/                  # Owner management module (includes FlatOwner junction)
│   ├── __init__.py, apps.py, models.py, views.py, forms.py, urls.py, admin.py
│
├── tenants/                 # Tenant management module
│   ├── __init__.py, apps.py, models.py, views.py, forms.py, urls.py, admin.py
│
├── templates/               # Shared templates
│   ├── base.html            # Base layout (Bootstrap 5, HTMX, blocks: title/content/scripts)
│   ├── home.html            # Home page
│   └── includes/
│       └── navbar.html      # Navigation bar partial
│
├── static/                  # Static files (CSS, JS, images) — create as needed
└── locale/                  # Translation files — create with `django-admin makemessages`
```

## Domain Model

- **Building** has many **Flats** (1:N)
- **Flat** has many **Owners** via **FlatOwner** junction table (M:N with ownership share and effective dates)
- **Flat** has many **Tenants** (1:N)
- **User** has a role: admin, chairman, board_member, or owner (see `core/permissions.py` → `Roles`)
- **User** optionally links to an **Owner** (1:1)
- **AuditLog** records every data change (immutable, append-only, via django-auditlog)

## Coding Conventions

### Python / Django
- Follow PEP 8 — enforced by Ruff (line-length = 120, see `pyproject.toml [tool.ruff]`)
- Use type hints for function signatures
- Use Django class-based views (ListView, DetailView, CreateView, UpdateView)
- Use Django ModelForm for all forms
- Use Django ORM — no raw SQL unless absolutely necessary
- Use `UUID` as primary key for all models (not auto-increment)
- All models inherit from `BaseModel` in `core/models.py` which provides:
  - `id` (UUIDField, primary key, auto-generated uuid4)
  - `created_at` (DateTimeField, auto_now_add)
  - `updated_at` (DateTimeField, auto_now)
  - Soft delete via `SafeDeleteModel` with `SOFT_DELETE_CASCADE` policy
- Register all models with audit trail using `@register_auditlog` decorator from `core/models.py`
- Naming: models in singular (`Building`, `Flat`, `Owner`, `Tenant`), apps in plural (`buildings`, `flats`, `owners`, `tenants`)
- Import sorting handled by Ruff (isort rules). Known first-party: `solomon`, `core`, `buildings`, `flats`, `owners`, `tenants`

### Environment & Configuration
- Use `django-environ` to load settings from `.env` file (see `solomon/settings/base.py`)
- Settings are split: `base.py` (shared) → `dev.py` / `prod.py` / `test.py` (environment-specific)
- `DJANGO_SETTINGS_MODULE` defaults to `solomon.settings.dev` (in `manage.py`)
- All secrets and environment-specific values go in `.env` (never commit `.env`, use `.env.example` as template)

### Templates
- Use Django template language (not Jinja2)
- Base template at `templates/base.html` with blocks: `title`, `content`, `extra_css`, `extra_js`
- Use HTMX attributes for dynamic behavior (hx-get, hx-post, hx-target, hx-swap)
- Keep templates simple — logic belongs in views, not templates
- Use Bootstrap 5 classes for layout and components
- Navigation in `templates/includes/navbar.html`

### Localization
- All user-facing strings must use Django translation: `{% trans %}` in templates, `_()` or `gettext_lazy()` in Python
- Czech is the primary language (locale: `cs`), English secondary (`en`)
- Date format: `d.m.Y` (Czech standard) — configured in `base.py`
- Currency: CZK (Kč)
- Never hardcode Czech strings — always use translation functions
- Translation files in `locale/` — generate with `django-admin makemessages -l cs`

### Database
- PostgreSQL 16 in production and Docker dev (via `docker-compose.yml`)
- SQLite acceptable for local development without Docker
- Connection via `DATABASE_URL` environment variable (parsed by django-environ)
- All migrations must be committed to the repository
- Use `effective_from` / `effective_to` date fields for temporal data (ownership, tenancy)
- Ownership share stored as `share_numerator` / `share_denominator` (integers, not float)
- Never hard-delete records — soft delete via django-safedelete (`SOFT_DELETE_CASCADE`)

## Authorization Rules

Four roles defined in `core/permissions.py` → `Roles` class:

| Role | Constant | Access |
|------|----------|--------|
| **admin** | `Roles.ADMIN` | Full CRUD on all data. Manages users. |
| **chairman** | `Roles.CHAIRMAN` | Full CRUD. Approves contracts above threshold. |
| **board_member** | `Roles.BOARD_MEMBER` | Full CRUD. Approves expenses and repairs. |
| **owner** | `Roles.OWNER` | Read-only on own data. Can submit change/repair requests. Cannot edit. |

- Management roles (full CRUD): `Roles.MANAGEMENT_ROLES` = `{ADMIN, CHAIRMAN, BOARD_MEMBER}`
- Use Django's built-in `Group` and `Permission` system
- Check permissions in views using `PermissionRequiredMixin` or `@permission_required`
- Owners must only see their own flats, their own tenants, their own audit trail
- Filter querysets based on user role in every view

## Audit Trail Requirements

- Every create, update, and delete operation must be logged automatically via django-auditlog
- Register models using `@register_auditlog` decorator from `core/models.py`
- Each audit log entry records: user, timestamp, entity type, entity ID, field name, old value, new value
- Audit log is immutable — never update or delete audit records
- If audit logging fails, the original operation must also fail (transactional)
- Use `effective_from` / `effective_to` fields on domain models to track when changes apply in the real world

## Testing

- **Framework:** pytest + pytest-django (configured in `pyproject.toml [tool.pytest.ini_options]`)
- **Settings:** Tests use `solomon.settings.test` (in-memory SQLite, fast password hasher)
- **Shared fixtures:** Root-level `conftest.py` provides `client`, `admin_client`, `admin_user`
- **Factories:** Use `factory_boy` for test data — create factories in `<app>/tests/factories.py`
- **Coverage:** pytest-cov with `fail_under = 70` (see `pyproject.toml [tool.coverage]`)
- **Test file naming:** `test_*.py` or `*_tests.py` (in each app's `tests/` directory)
- Test permission enforcement: verify owners cannot access other owners' data
- Test audit trail: verify changes are logged correctly
- Test soft delete: verify deleted records are excluded from queries but preserved in DB
- Test ownership share validation: warn if shares don't sum to 100%
- Run tests: `pytest` (or `pytest --cov` for coverage report)

## Development Workflow

### Local Setup (without Docker)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # Edit as needed
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Local Setup (with Docker)
```bash
docker compose up -d            # PostgreSQL + Django on localhost:8000
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

### Debugging
- Port 5678 is exposed in docker-compose for `debugpy` attachment
- Django Debug Toolbar available in dev (auto-added via `settings/dev.py`)

### Pre-commit
```bash
pre-commit install              # One-time setup
pre-commit run --all-files      # Manual run
```

## Git Conventions

- Branch naming: `feature/module-name`, `fix/description`, `docs/description`
- Commit messages: imperative mood, e.g., "Add building model", "Fix owner permission check"
- Keep commits focused — one logical change per commit
- Always run tests before pushing (`pytest`)
- Pre-commit hooks auto-run on `git commit` (ruff lint, ruff format, mypy)

## Key Business Rules (Reference)

1. One building contains many flats. Each flat belongs to exactly one building.
2. One owner can own multiple flats. One flat can have multiple owners (co-ownership).
3. Ownership shares per flat should sum to 100% (warn if not, don't block).
4. One flat can have multiple tenants. Tenants are linked to flats, not directly to owners.
5. All ownership and tenancy changes require an effective date (`effective_from` / `effective_to`).
6. Soft delete everywhere — never hard-delete data (django-safedelete with `SOFT_DELETE_CASCADE`).
7. All data changes are recorded in an immutable audit trail (django-auditlog with `@register_auditlog`).
8. Chairman has special approval rights for contracts above a configurable monetary threshold.
9. Individual owners can only view their own data and submit requests — they cannot edit anything directly.
