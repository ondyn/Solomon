# ============================================================================
# Solomon — Makefile
# All common development tasks in one place.
# Usage: make <target>   (run `make help` to see all targets)
# ============================================================================

.DEFAULT_GOAL := help
.PHONY: help install sync env init migrate createsuperuser run run-debug \
        test test-cov lint format typecheck check pre-commit messages \
        docker-build docker-up docker-down docker-restart docker-logs \
        docker-migrate docker-createsuperuser docker-shell docker-rebuild \
        prod-build prod-up prod-down clean

# Colors for help
BLUE  := \033[36m
RESET := \033[0m

# ============================================================================
# Help
# ============================================================================

help: ## Show this help message
	@echo "Solomon — Development Tasks"
	@echo "==========================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ============================================================================
# Local Development (without Docker)
# ============================================================================

install: ## Install uv (if not present) — run once
	@command -v uv >/dev/null 2>&1 || { \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@echo "uv is installed: $$(uv --version)"

sync: ## Install/sync all dependencies (creates .venv automatically)
	uv sync

env: ## Create .env from .env.example (if .env doesn't exist)
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example — edit it as needed"; \
	else \
		echo ".env already exists — skipping"; \
	fi

init: install sync env migrate ## Full project setup: install uv, sync deps, create .env, run migrations
	@echo ""
	@echo "✅  Project initialized! Next steps:"
	@echo "  make createsuperuser   — create admin account"
	@echo "  make run               — start development server"

migrate: ## Run Django migrations
	uv run python manage.py migrate

makemigrations: ## Create new Django migrations
	uv run python manage.py makemigrations

createsuperuser: ## Create Django superuser
	uv run python manage.py createsuperuser

run: ## Start Django development server (localhost:8000)
	uv run python manage.py runserver

run-debug: ## Start Django with debugpy (attach on port 5678)
	uv run python -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000

shell: ## Open Django interactive shell (IPython)
	uv run python manage.py shell

collectstatic: ## Collect static files
	uv run python manage.py collectstatic --noinput

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run Ruff linter (with auto-fix)
	uv run ruff check --fix .

format: ## Run Ruff formatter
	uv run ruff format .

typecheck: ## Run mypy type checker
	uv run mypy .

check: lint format typecheck ## Run all checks: lint + format + typecheck

pre-commit: ## Run all pre-commit hooks
	uv run pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks (one-time setup)
	uv run pre-commit install

# ============================================================================
# Testing
# ============================================================================

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage report
	uv run pytest --cov --cov-report=term-missing

test-fast: ## Run tests excluding slow-marked tests
	uv run pytest -m "not slow"

test-verbose: ## Run tests with verbose output
	uv run pytest -vv

# ============================================================================
# Localization
# ============================================================================

messages: ## Generate/update Czech translation files
	uv run django-admin makemessages -l cs

compilemessages: ## Compile translation files
	uv run django-admin compilemessages

# ============================================================================
# Docker Development
# ============================================================================

docker-build: ## Build Docker images (development target)
	docker compose build

docker-up: ## Start Docker services (PostgreSQL + Django)
	docker compose up -d

docker-down: ## Stop Docker services
	docker compose down

docker-restart: docker-down docker-up ## Restart Docker services

docker-logs: ## Tail Docker logs
	docker compose logs -f

docker-migrate: ## Run migrations inside Docker
	docker compose exec web uv run python manage.py migrate

docker-createsuperuser: ## Create superuser inside Docker
	docker compose exec web uv run python manage.py createsuperuser

docker-shell: ## Open Django shell inside Docker
	docker compose exec web uv run python manage.py shell

docker-bash: ## Open bash shell inside Docker web container
	docker compose exec web bash

docker-rebuild: ## Full rebuild: stop, rebuild images, start
	docker compose down
	docker compose build --no-cache
	docker compose up -d

docker-init: docker-build docker-up docker-migrate ## Docker full setup: build, start, migrate
	@echo ""
	@echo "✅  Docker environment ready! Next steps:"
	@echo "  make docker-createsuperuser   — create admin account"
	@echo "  Open http://localhost:8000"

# ============================================================================
# Docker Production
# ============================================================================

prod-build: ## Build production Docker image
	docker compose -f docker-compose.yml build --target production

prod-up: ## Start production services
	docker compose -f docker-compose.yml up -d

prod-down: ## Stop production services
	docker compose -f docker-compose.yml down

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove build artifacts, caches, and .pyc files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "Cleaned build artifacts"

clean-all: clean ## Remove everything including .venv and db.sqlite3
	rm -rf .venv
	rm -f db.sqlite3
	@echo "Cleaned .venv and database"
