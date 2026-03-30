# ============================================================================
# Solomon — Docker environment (uses uv for fast dependency management)
# Multi-stage build: base → builder → production / development
# ============================================================================

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        gettext \
    && rm -rf /var/lib/apt/lists/*

# Install uv — fast Python package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ---- Builder stage (production dependencies only) ----
FROM base AS builder

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ---- Production stage ----
FROM base AS production

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["gunicorn", "solomon.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

# ---- Development stage ----
FROM base AS development

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .

EXPOSE 8000 5678

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
