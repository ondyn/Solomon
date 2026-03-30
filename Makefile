# ============================================================================
# Solomon - Makefile (Docker-first development)
# All development runs inside Docker.
# Usage: make <target>   (run `make help` to see all targets)
# ============================================================================

.DEFAULT_GOAL := help
.PHONY: help init up down restart logs build rebuild \
	run debug migrate makemigrations createsuperuser shell bash \
	test test-cov test-fast test-verbose \
	lint format typecheck check pre-commit pre-commit-install \
	messages compilemessages collectstatic \
	db-backup db-restore db-reset db-psql \
	prod-build prod-up prod-down \
	clean clean-all

BLUE  := \033[36m
RESET := \033[0m
DC    := docker compose
BACKUP_DIR := ./backups
BACKUP_FILE ?= $(BACKUP_DIR)/solomon_$(shell date +%Y%m%d_%H%M%S).sql.gz

# ============================================================================
# Help
# ============================================================================

help: ## Show this help message
	@echo "Solomon - Development Tasks (Docker-first)"
	@echo "============================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "  Database backup/restore:"
	@echo "    make db-backup                         - backup to backups/solomon_<timestamp>.sql.gz"
	@echo "    make db-backup BACKUP_FILE=my.sql.gz   - backup to custom file"
	@echo "    make db-restore FILE=backups/xxx.sql.gz - restore from file"
	@echo ""

# ============================================================================
# Docker Lifecycle
# ============================================================================

init: build up migrate ## Full setup: build, start, migrate
	@echo ""
	@echo "Project initialized!"
	@echo "  App running at: http://localhost:8000"
	@echo ""
	@echo "  Next steps:"
	@echo "    make createsuperuser   - create admin account"
	@echo "    make logs              - watch server output"

build: ## Build Docker images
	$(DC) build

up: ## Start all services (Django + PostgreSQL)
	$(DC) up -d
	@echo ""
	@echo "Solomon is running at http://localhost:8000"
	@echo "Django auto-reloads on every .py file change."
	@echo "Run make logs to see server output."

run: up ## Alias for up

down: ## Stop all services
	$(DC) down

restart: down up ## Restart all services

logs: ## Tail logs (Ctrl+C to stop)
	$(DC) logs -f

debug: ## Start with debugpy - attach VS Code on port 5678
	$(DC) stop web 2>/dev/null || true
	$(DC) run --rm --name solomon-debug --service-ports web uv run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client manage.py runserver 0.0.0.0:8000

rebuild: ## Full rebuild (no cache)
	$(DC) down
	$(DC) build --no-cache
	$(DC) up -d

# ============================================================================
# Django Management (runs inside Docker)
# ============================================================================

migrate: ## Run Django migrations
	$(DC) exec web uv run python manage.py migrate

makemigrations: ## Create new Django migrations
	$(DC) exec web uv run python manage.py makemigrations

createsuperuser: ## Create Django superuser
	$(DC) exec web uv run python manage.py createsuperuser

shell: ## Open Django interactive shell
	$(DC) exec web uv run python manage.py shell

bash: ## Open bash in web container
	$(DC) exec web bash

collectstatic: ## Collect static files
	$(DC) exec web uv run python manage.py collectstatic --noinput

# ============================================================================
# Code Quality (runs inside Docker)
# ============================================================================

lint: ## Run Ruff linter (with auto-fix)
	$(DC) exec web uv run ruff check --fix .

format: ## Run Ruff formatter
	$(DC) exec web uv run ruff format .

typecheck: ## Run mypy type checker
	$(DC) exec web uv run mypy .

check: lint format typecheck ## Run all: lint + format + typecheck

pre-commit: ## Run all pre-commit hooks
	$(DC) exec web uv run pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	$(DC) exec web uv run pre-commit install

# ============================================================================
# Testing (runs inside Docker)
# ============================================================================

test: ## Run tests
	$(DC) exec web uv run pytest

test-cov: ## Run tests with coverage
	$(DC) exec web uv run pytest --cov --cov-report=term-missing

test-fast: ## Run tests (skip slow)
	$(DC) exec web uv run pytest -m "not slow"

test-verbose: ## Run tests (verbose)
	$(DC) exec web uv run pytest -vv

# ============================================================================
# Localization (runs inside Docker)
# ============================================================================

messages: ## Generate Czech translation files
	$(DC) exec web uv run django-admin makemessages -l cs

compilemessages: ## Compile translation files
	$(DC) exec web uv run django-admin compilemessages

# ============================================================================
# Database Backup and Restore
# ============================================================================

db-backup: ## Backup database to backups/ directory
	@mkdir -p $(BACKUP_DIR)
	$(DC) exec db pg_dump -U solomon solomon | gzip > $(BACKUP_FILE)
	@echo "Database backed up to: $(BACKUP_FILE)"

db-restore: ## Restore from backup (make db-restore FILE=backups/xxx.sql.gz)
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make db-restore FILE=backups/solomon_YYYYMMDD_HHMMSS.sql.gz"; \
		echo ""; \
		echo "Available backups:"; \
		ls -la $(BACKUP_DIR)/*.sql.gz 2>/dev/null || echo "  (none found)"; \
		exit 1; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "File not found: $(FILE)"; \
		exit 1; \
	fi
	@echo "This will DROP and recreate the solomon database!"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(DC) exec db dropdb -U solomon --if-exists solomon
	$(DC) exec db createdb -U solomon solomon
	gunzip -c $(FILE) | $(DC) exec -T db psql -U solomon solomon
	@echo "Database restored from: $(FILE)"

db-reset: ## Drop and recreate empty database + migrate
	@echo "This will DESTROY all data in the database!"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(DC) exec db dropdb -U solomon --if-exists solomon
	$(DC) exec db createdb -U solomon solomon
	$(DC) exec web uv run python manage.py migrate
	@echo "Database reset and migrations applied."

db-psql: ## Open psql shell
	$(DC) exec db psql -U solomon solomon

# ============================================================================
# Production
# ============================================================================

prod-build: ## Build production Docker image
	docker build --target production -t solomon:prod .

prod-up: ## Start production services
	$(DC) -f docker-compose.yml up -d

prod-down: ## Stop production services
	$(DC) -f docker-compose.yml down

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove Python caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "Cleaned build artifacts"

clean-all: clean down ## Remove everything + Docker volumes
	$(DC) down -v
	rm -rf .venv
	rm -f db.sqlite3
	@echo "Cleaned everything (Docker volumes removed)"
