# ============================================================================
# Solomon — Docker development environment
# Multi-stage build: builder → production
# ============================================================================

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        gettext \
    && rm -rf /var/lib/apt/lists/*

# ---- Builder stage ----
FROM base AS builder

# Install build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install .

# ---- Production stage ----
FROM base AS production

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["gunicorn", "solomon.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

# ---- Development stage ----
FROM base AS development

COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install ".[dev]"

COPY . .

EXPOSE 8000 5678

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
