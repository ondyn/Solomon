# Solomon — GitHub Copilot Instructions

## Project Overview

Solomon is a **facility management system** for managing apartment buildings under SVJ (Společenství vlastníků jednotek) in the Czech Republic. It manages buildings, flats, owners, tenants, and provides a full audit trail of all changes.

**Repository:** github.com/ondyn/Solomon
**Design Document:** See `DESIGN.md` for full architecture, data model, and requirements.

## Tech Stack

- **Backend:** Django 5.x (Python 3.12+)
- **Frontend:** Django Templates + HTMX + Bootstrap 5 (or Tailwind CSS)
- **Database:** PostgreSQL (SQLite for local development)
- **Key packages:** django-auditlog, django-safedelete, django-htmx
- **Localization:** Czech (cs) primary, multi-language via Django i18n
- **Deployment:** Docker, GitHub Actions CI/CD

## Project Structure

```
solomon/
  manage.py
  solomon/              # Django project (settings, urls, wsgi)
  core/                 # Shared: base models, audit, auth, permissions, middleware
  buildings/            # Building management module (Django app)
  flats/                # Flat management module (Django app)
  owners/               # Owner management module (Django app)
  tenants/              # Tenant management module (Django app)
  templates/            # Shared templates (base.html, navbar, etc.)
  locale/cs/            # Czech translations
  static/               # CSS, JS, images
```

Each module (buildings, flats, owners, tenants) is a separate Django app with its own models, views, forms, templates, and URLs.

## Domain Model

- **Building** has many **Flats** (1:N)
- **Flat** has many **Owners** via **FlatOwner** junction table (M:N with ownership share and effective dates)
- **Flat** has many **Tenants** (1:N)
- **User** has a role: admin, chairman, board_member, or owner
- **User** optionally links to an **Owner** (1:1)
- **AuditLog** records every data change (immutable, append-only)

## Coding Conventions

### Python / Django
- Follow PEP 8 style guide
- Use type hints for function signatures
- Use Django class-based views (ListView, DetailView, CreateView, UpdateView)
- Use Django ModelForm for all forms
- Use Django ORM — no raw SQL unless absolutely necessary
- Use `UUID` as primary key for all models (not auto-increment)
- All models inherit from a `BaseModel` in `core/models.py` that provides:
  - `id` (UUIDField, primary key)
  - `created_at` (DateTimeField, auto_now_add)
  - `updated_at` (DateTimeField, auto_now)
  - `is_deleted` (BooleanField, default=False) — soft delete via django-safedelete
- Use django-auditlog for automatic audit trail on all models
- Naming: models in singular (`Building`, `Flat`, `Owner`, `Tenant`), apps in plural (`buildings`, `flats`, `owners`, `tenants`)

### Templates
- Use Django template language (not Jinja2)
- Base template at `templates/base.html` with blocks: title, content, scripts
- Use HTMX attributes for dynamic behavior (hx-get, hx-post, hx-target, hx-swap)
- Keep templates simple — logic belongs in views, not templates
- Use Bootstrap 5 classes for layout and components

### Localization
- All user-facing strings must use Django translation: `{% trans %}` in templates, `_()` or `gettext_lazy()` in Python
- Czech is the primary language (locale: `cs`)
- Date format: `d.m.Y` (Czech standard)
- Currency: CZK (Kč)
- Never hardcode Czech strings — always use translation functions

### Database
- PostgreSQL in production, SQLite acceptable for local development
- All migrations must be committed to the repository
- Use `effective_from` / `effective_to` date fields for temporal data (ownership, tenancy)
- Ownership share stored as `share_numerator` / `share_denominator` (integers, not float)
- Never hard-delete records — use soft delete (`is_deleted = True`)

## Authorization Rules

Four roles with different permissions:

| Role | Access |
|------|--------|
| **admin** | Full CRUD on all data. Manages users. |
| **chairman** | Full CRUD. Approves contracts above threshold. |
| **board_member** | Full CRUD. Approves expenses and repairs. |
| **owner** | Read-only on own data. Can submit change/repair requests. Cannot edit. |

- Use Django's built-in `Group` and `Permission` system
- Check permissions in views using `PermissionRequiredMixin` or `@permission_required`
- Owners must only see their own flats, their own tenants, their own audit trail
- Filter querysets based on user role in every view

## Audit Trail Requirements

- Every create, update, and delete operation must be logged automatically
- Each audit log entry records: user, timestamp, entity type, entity ID, field name, old value, new value, effective date
- Audit log is immutable — never update or delete audit records
- If audit logging fails, the original operation must also fail (transactional)
- The `effective_date` field represents when the change applies in the real world (may differ from `recorded_at`)

## Testing

- Write tests for all models, views, and business logic
- Use `django.test.TestCase` for database tests
- Use `factory_boy` for test data factories
- Test permission enforcement: verify owners cannot access other owners' data
- Test audit trail: verify changes are logged correctly
- Test soft delete: verify deleted records are excluded from queries but preserved in DB
- Test ownership share validation: warn if shares don't sum to 100%

## Git Conventions

- Branch naming: `feature/module-name`, `fix/description`, `docs/description`
- Commit messages: imperative mood, e.g., "Add building model", "Fix owner permission check"
- Keep commits focused — one logical change per commit
- Always run tests before pushing

## Key Business Rules (Reference)

1. One building contains many flats. Each flat belongs to exactly one building.
2. One owner can own multiple flats. One flat can have multiple owners (co-ownership).
3. Ownership shares per flat should sum to 100% (warn if not, don't block).
4. One flat can have multiple tenants. Tenants are linked to flats, not directly to owners.
5. All ownership and tenancy changes require an effective date.
6. Soft delete everywhere — never hard-delete data.
7. All data changes are recorded in an immutable audit trail.
8. Chairman has special approval rights for contracts above a configurable monetary threshold.
9. Individual owners can only view their own data and submit requests — they cannot edit anything directly.
